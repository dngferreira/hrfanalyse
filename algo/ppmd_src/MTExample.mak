## Take a look at PPMdType.h for additional compiler & environment options
.AUTODEPEND
#               User defined variables
PRJNAME=MTExample
DEBUG=0
CPP_SET=$(PRJNAME).cpp Model.cpp
C_SET=
.path.cpp = ;
#               End of user defined variables

CC     = Bcc32
TLINK  = TLink32
ECFLAG = -WX -f- -a4 -tWM -D_USE_THREAD_KEYWORD
ELFLAG = /Tpe /ax
STARTM = c0x32.obj
LIBS   = noeh32.lib cw32mt.lib import32.lib

!if $(DEBUG) != 0
    DCFLAG = -v -vi -N
    DLFLAG = /v /s
!else
    DCFLAG = -Oa2 -k- -N-
!endif

SCFLAG  = -w -w-sig -w-inl -H=$(PRJNAME).csm -6 -Vmd -x- -RT-
SLFLAG  = /x /c
OBJ_SET = $(CPP_SET:.cpp=.obj) $(C_SET:.c=.obj)

$(PRJNAME).exe : $(OBJ_SET)
  @$(TLINK)    @&&|
$(SLFLAG) $(ELFLAG) $(DLFLAG) $(STARTM) $(OBJ_SET),$(PRJNAME).exe,,$(LIBS)
|

.cpp.obj:
    @$(CC) $(SCFLAG) $(ECFLAG) $(DCFLAG) -c {$< }

.c.obj:
    @$(CC) $(SCFLAG) $(ECFLAG) $(DCFLAG) -c {$< }
