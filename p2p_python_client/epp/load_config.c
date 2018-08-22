


#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CONFIG_FILE_A1 "./config/dl645_07_a1.csv"
#define CONFIG_FILE_A2 "dl645_07_a2.csv"
#define CONFIG_FILE_A3 "dl645_07_a3.csv"
#define CONFIG_FILE_A4 "dl645_07_a4.csv"
#define CONFIG_FILE_A5 "dl645_07_a5.csv"
#define CONFIG_FILE_A6 "dl645_07_a6.csv"
#define CONFIG_FILE_A7 "dl645_07_a7.csv"


#define UNIT_KWH        0x01    //kWh
#define UNIT_KVA        0x02    //kVA
#define UNIT_KVAR       0x03    //kvar
#define UNIT_KVAH       0x04    //kVAh
#define UNIT_KVARH      0x05    //kvarh
#define UNIT_DATE       0x06    //日期,年月日时分
#define UNIT_VALUE_DATE    0x07    //year_date ，包含日期的数据

#define UNIT_V          0x10    //V
#define UNIT_A          0x11    //A
#define UNIT_PERCENT    0X12    //%
#define UNIT_TIMES      0X13    //次
#define UNIT_UNKNOW     0xFF    //未知

#define	s08bits	char
#define	s16bits	int16_t
#define	s32bits	int32_t
#define	s64bits	int64_t

#define	u08bits	unsigned char
#define	u16bits uint16_t
#define	u32bits	uint32_t
#define	u64bits	uint64_t


#define CONFIG_CAT_A1 0x00
#define CONFIG_CAT_A2 0x01
#define CONFIG_CAT_A3 0x02
#define CONFIG_CAT_A4 0x03
#define CONFIG_CAT_A5 0x04
#define CONFIG_CAT_A6 0x05
#define CONFIG_CAT_A7 0x06

typedef struct _st_cat_unit_defines {
    u08bits key[4];     //数据标识 DI3,DI2,DI1,DI0
    u08bits key_type;   // 03-> key[2]为变量，嵌入到data_des ...中。04->;
    u08bits key_stt;    //key中 1...0A   1
    u08bits key_end;    //key中 1...0A   0A
    u08bits length;     //数据长度
    u08bits unit;       //单位
    s08bits * des;      //中文描述 带...要替换
    struct _st_cat_unit_defines *next;
}st_cat_unit_defines_t;

// struct _st_cat_defines{
//     u08bits len;
//     st_cat_unit_defines_t *body;
// };




static struct _st_cat_defines{
    u08bits di3;
    st_cat_unit_defines_t *config;
    s08bits *config_file;
}cat_configs[]={
    {CONFIG_CAT_A1,NULL,CONFIG_FILE_A1},
    {CONFIG_CAT_A2,NULL,CONFIG_FILE_A2},
    {CONFIG_CAT_A3,NULL,CONFIG_FILE_A3},
    {CONFIG_CAT_A4,NULL,CONFIG_FILE_A4},
    {CONFIG_CAT_A5,NULL,CONFIG_FILE_A5},
    {CONFIG_CAT_A6,NULL,CONFIG_FILE_A6},
    {CONFIG_CAT_A7,NULL,CONFIG_FILE_A7},
    {0xFF,NULL,NULL}
};


s08bits ** get_line_array(s08bits *line,u08bits * det){

    s08bits **res_array=(s08bits **) malloc(10 * sizeof(s08bits *));

    bzero(res_array,sizeof(10 * sizeof(s08bits *)+1));

    int i = 1;
    res_array[0] = NULL; //待free;

    res_array[i] = strsep(&line,det);
    
    for(;res_array[i] != NULL;){

        if (i >9){
            perror("over 9");
            exit(EXIT_FAILURE);
        }  
        i++;
        res_array[i] = strsep(&line,det);        
    }

    return res_array;

}



static struct _st_unit_st{
    u08bits unit;
    s08bits * des;
}unit_des[]={
    {UNIT_KWH,"kWh"},
    {UNIT_KVA,"kVA"},
    {UNIT_KVAR,"kvar"},
    {UNIT_KVAH,"kVAh"},
    {UNIT_KVARH,"kvarh"},
    {UNIT_VALUE_DATE,"value_date"},//日期,年月日时分
    {UNIT_V,"V"},
    {UNIT_A,"A"},
    {UNIT_PERCENT,"%"},
    {UNIT_TIMES,"次"},
    {0,NULL}

};


u08bits get_unit(s08bits *unit){

    int i = 0;

    for(;unit_des[i].des !=NULL;i++){
        if(strstr(unit,unit_des[i].des) !=NULL){
            return unit_des[i].unit;
        }
    }

    return UNIT_UNKNOW;
}


int set_cat_key(s08bits *line[],st_cat_unit_defines_t *cat){

    cat->key[0] = strtol(line[1] ,NULL,16);
    cat->key[1] = strtol(line[2] ,NULL,16);
    cat->key[2] = strtol(line[3] ,NULL,16);
    cat->key[3] = strtol(line[4] ,NULL,16);

    if((cat->key_type= strtol(line[8],NULL,16))>0){
        if(cat->key_type >4) return -1;
            s08bits *stt ,*tmp;
            stt = tmp = line[(cat->key_type & 0x07)];

            if((tmp =strstr(stt,"...")) != NULL){
                cat->key_stt = strtol(stt,NULL,16);
                cat->key_end = strtol(tmp+3,NULL,16);
                cat->key[cat->key_type-1] = 0xee; //默认设定为0xee
            }
         
    }
    cat->next = NULL;
    return 0;

}

void free_line(s08bits **line_arr){

    int i = 8;

    for(;i !=0;i--)
      free(line_arr[i]);

}


st_cat_unit_defines_t * set_cat_unit(u08bits * line){
    st_cat_unit_defines_t *new_cat = (st_cat_unit_defines_t *) malloc(sizeof(st_cat_unit_defines_t));
    
    bzero(new_cat,sizeof(st_cat_unit_defines_t));

    s08bits **line_arr =  get_line_array(line,",");

    set_cat_key(line_arr,new_cat);

    new_cat->length = strtol(line_arr[6],NULL,16);
    new_cat->unit = get_unit(line_arr[7]);
    new_cat->des = strdup(line_arr[9]);



}


st_cat_unit_defines_t * cat_config_init(char *path ){
    FILE * fp;
    char * line = NULL;
    size_t len = 0;
    ssize_t read;

    st_cat_unit_defines_t * cat_cnf=NULL ,*tmp_cat = NULL;

    fp = fopen(path, "rb");
    if (fp == NULL)
        exit(EXIT_FAILURE);

    while ((read = getline(&line, &len, fp)) != -1) {
        printf("%s", line);
        if (NULL == cat_cnf)
            tmp_cat = cat_cnf = set_cat_unit(line);
        else{
            tmp_cat->next = set_cat_unit(line);
            tmp_cat =  tmp_cat->next;
            tmp_cat ->next = NULL;
        }
    }

    fclose(fp);
    if (line)
        free(line);
    //exit(EXIT_SUCCESS);

    return cat_cnf;

}


void test(u08bits config_cat){

    st_cat_unit_defines_t *config = cat_configs[config_cat].config;

    st_cat_unit_defines_t *tmp_cnf = config;

    while(tmp_cnf){
        printf("%02x,%02x,%02x,%02x,length[%d],stt[%d],end[%d], des[%s]\n",
            tmp_cnf->key[0],tmp_cnf->key[1],tmp_cnf->key[2],tmp_cnf->key[3],
            tmp_cnf->length,tmp_cnf->key_stt,tmp_cnf->key_end,
            tmp_cnf->des);

        tmp_cnf = tmp_cnf->next;
    }
    
}

int main(void){

    int i=0;

    for(;cat_configs[i].di3 != 0xFF;i++){
        cat_configs[i].config = cat_config_init(cat_configs[i].config_file);
    }
    test(CONFIG_CAT_A1);
    test(CONFIG_CAT_A2);
    test(CONFIG_CAT_A3);
    test(CONFIG_CAT_A4);
    test(CONFIG_CAT_A5);
    test(CONFIG_CAT_A6);


        

    return 0;

}