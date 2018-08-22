/**
 The enumeration defines errors that are throw UDPClient methods
 ````
 noSocket              Error thrown if a socket file descriptor could not be created
 bindSocket            Error thrown if the bind process fails for the socket file descriptor
 badAddress            Error thrown if the address string given is not proper
 alreadyInProgress     Error thrown if beginOperation() is called on a UPDClient object who's receive/send process currently running
 setupForNonBlocking   Error thrown if the init method fails to set the socket for non-blocking operation
 threadLock            Error thrown if the init method fails to obtain a valid thread lock
 
 - parameter localizedDescription: Explanation of the current error
 */
enum UDPClientError: Int, LocalizedError {
    
    case noSocket = -999
    case bindSocket
    case badAddress
    case alreadyInProgress
    case setupForNonBlocking
    case threadLock
    
    var localizedDescription: String {
        
        switch self {
            
        case .alreadyInProgress:
            return "operation in progress"
        case .badAddress:
            return "Address string given is not valid"
        case .bindSocket:
            return "Could not bind socket"
        case .noSocket:
            return "Could not obtain socket"
        case .setupForNonBlocking:
            return "Could not setup socket for non-blocking operation"
        case .threadLock:
            return "Could not obtain thread lock"
        }
        
    }
}
 
/**
 This class defines objects that can be created to send and receive UDP messages
 */
class UDPClient {
    
    // MARK: - properties
    // socket file descriptor
    private var mySocket: Int32 = 0
    // socket address for the client
    private var myAddress = sockaddr_in()
    // socket address for the target client
    private var otherAddress = sockaddr_in()
    // Holds messages received and read by the Rx/Tx thread method
    private var receiveQueue = [String]()
    // Holds messages to be transmitted in the Rx/Tx thread method
    private var sendQueue = [String]()
    // flag controls the execute loop with the Rx/Tx thread method
    private var okToRun = false
    // thread mutex resource
    private var threadLock = pthread_mutex_t()
    // limit for sent and received message
    private let BufferLimit = 1024
    // name for this client
    let name: String
    
    // MARK: - initialization and de-initialization
    /**
     Designated initializater
     
     - parameters:
        - name:             Client's name
        - port:             The client's port
        - otherIPAddress:   The IPv4 address of the recipient's machine
        - otherPort:        The port the recipient will be listening for the client's message
     
     - throws:A UDPClientError on failure
     */
    init(name: String, port: UInt16, otherIPAddress: String, otherPort: UInt16) throws {
        
        // assign
        self.name = name
        
        // get a socket file descriptor
        mySocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)

        // no socket
        if mySocket == -1 {
            throw UDPClientError.noSocket
        }
        
        // set the socket as non-blocking, else throw error
        if fcntl(mySocket, F_SETFL, O_NONBLOCK) == -1 {
            
            throw UDPClientError.setupForNonBlocking
        }
        
        // configure the client's socket address
        myAddress.sin_family = sa_family_t(AF_INET)
        myAddress.sin_port = in_port_t(port)
        myAddress.sin_addr.s_addr = in_addr_t(INADDR_ANY)
        
        // bind the socket to the socket address
        let retCode = withUnsafeMutablePointer(to: &myAddress) {
            
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                
                bind(mySocket, UnsafeMutablePointer<sockaddr>($0), socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        // throw error if the socket could not be bound to the socket address
        if retCode == -1 {
            
            throw UDPClientError.bindSocket
        }
        
        // configure recipient's address
        otherAddress.sin_family = sa_family_t(AF_INET)
        otherAddress.sin_port = in_port_t(otherPort)
        // need a buffer
        var buffer: [Int8] = Array(otherIPAddress.utf8CString)
        // copy address, throw error on failure
        if inet_aton(&buffer, &otherAddress.sin_addr) == 0 {
                
            throw UDPClientError.badAddress
        }
        // obtain mutex and throw error if we fail to obtain one
        if pthread_mutex_init(&threadLock, nil) != 0 {
            
            throw UDPClientError.threadLock
        }
    }
    
    /**
     Necessary cleanup performed in this method
     */
    deinit {
 
        pthread_mutex_unlock(&threadLock)
        
        pthread_mutex_destroy(&threadLock)
        
        close(mySocket)
    }
    
    // MARK: - methods
    /**
     This method kicks off the receive and transmit thread.
     - throws: A UDPClientError if the method is called and the receive/transmit operation is already in progress
     */
    func beginOperation() throws {
        
        // Rx/Tx thread process already running
        if okToRun {
            
            throw UDPClientError.alreadyInProgress
        }
        
        // set the flag, detach and start Rx/Tx thread
        okToRun = true
        _ = Thread.detachNewThreadSelector(#selector(process), toTarget: self, with: nil)        
    }
    
    /**
     This method stops the receive and transmit operation for the client
     */
    func endOperation() {
        
        okToRun = false
    }
    
    /**
     The method adds the desired message to the send queue
     - parameter message: Desired message to be transmitted
     */
    func send(message: String) {
        
        pthread_mutex_lock(&threadLock)
        
        sendQueue.append(message)
        
        pthread_mutex_unlock(&threadLock)
        
    }
    
    /**
     This method retrieves one message from the receive queue. Message are retreived in a first in, first out manner.
     - returns: The message at the front of the receive queue, or nil if the receive queue is empty
     */
    func getMessage() -> String? {
        
        var message: String?
        
        pthread_mutex_lock(&threadLock)
        // do we have any messages?
        if receiveQueue.isEmpty == false {
            
            message = receiveQueue.remove(at: 0)
        }
        
        pthread_mutex_unlock(&threadLock)
        
        return message
    }
    
    // MARK: - private thread process
    /**
     The method is run in a separate dedicated thread. This method contains a loop that handles both the receive
     and transmit of a message for the client
     */
    @objc private func process() {
        
        // buffers for Rx and Tx
        var sendBuffer = [UInt8](repeating: 0, count: BufferLimit)
        var receiveBuffer = [UInt8](repeating: 0, count: BufferLimit)
        // struct size, needed for revcfrom() and sendto() functions
        var slen = socklen_t(MemoryLayout<sockaddr_in>.size)
        
        print("Process running for " + name)
        
        // holds the number of bytes read and received
        var bytesRead = 0
        var bytesSent = 0
        
        /* MAIN PROCESS LOOP */
        while okToRun {
            
            // are there any messages to send?
            if sendQueue.isEmpty == false {
                // get a single message, from the front
                pthread_mutex_lock(&threadLock)
                
                var str = sendQueue.remove(at: 0)
                
                pthread_mutex_unlock(&threadLock)
                // message cannot be longer than buffer limit
                if str.characters.count > BufferLimit {
                    
                    let index = str.index(str.startIndex, offsetBy: BufferLimit)
                    str = str.substring(to: index)
                    sendBuffer.replaceSubrange(0 ..< BufferLimit, with: str.utf8)
                }
                else {
                    
                    sendBuffer.replaceSubrange(0 ..< str.characters.count, with: str.utf8)
                }
                // send message to recipient
                bytesSent = withUnsafeMutablePointer(to: &otherAddress) {
                    
                    $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                        
                        sendto(mySocket, sendBuffer, str.characters.count, 0, $0, slen)
                    }
                }
                // successfully sent message
                if bytesSent != -1 {
                    
                    print("\(name): bytes sent = \(bytesSent)")
                }
                // reset buffer
                sendBuffer = [UInt8](repeating: 0, count: BufferLimit)
            }
            // read message, can be no longer than buffer limit
            bytesRead = withUnsafeMutablePointer(to: &otherAddress) {
                
                $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                    
                    recvfrom(mySocket, &receiveBuffer, BufferLimit, 0, $0, &slen)
                }
            }
            // successfully read message
            if bytesRead != -1 {
                
                print("\(name): bytes read = \(bytesRead)")
                // add received message to queue
                pthread_mutex_lock(&threadLock)
                
                receiveQueue.append(String(bytes: receiveBuffer, encoding: .utf8)!)
                
                pthread_mutex_unlock(&threadLock)
                
                slen = socklen_t(MemoryLayout<sockaddr_in>.size)
                // reset buffer
                receiveBuffer = [UInt8](repeating: 0, count: BufferLimit)
            }
            // reset byte counts
            bytesRead = 0
            bytesSent = 0
            
        } // end processing loop
        
    } // end process
    
}