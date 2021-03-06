# -*- coding: utf-8 -*-
# Copyright (c) 2022, Harry Huang
# @ BSD 3-Clause License
import os.path, time
try:
    from osTool import *
    from colorTool import *
except:
    from .osTool import *
    from .colorTool import *
import UnityPy as Upy #UnityPy库用于操作Unity文件
'''
Python批量解包Unity(.ab)资源文件
'''


def ab_reslove(env, intodir:str, doimg:bool, dotxt:bool, doaud:bool, docover:bool, detail:bool):
    '''
    #### 解包ab文件env实例
    :param env:     UnityPy.load()创建的environment实例;
    :param intodir: 解包目的地的目录;
    :param doimg:   是否导出图片资源;
    :param dotxt:   是否导出文本资源;
    :param doaud:   是否导出音频资源;
    :param docover: 是否覆盖重名的已存在的文件，建议False，否则可能出现意外;
    :param detail:  是否回显详细信息；
    :returns:       (int) 已导出的文件数;
    '''
    mkdir(intodir)
    if detail:
        print(color(2)+"  找到了", len(env.objects), "个资源，正在处理...")
    cont_s = 0 #已导出资源计数
    ospath = os.path
    ###
    for i in env.objects:
        #(i是env实例中的单个object)
        succ = False #是否成功导出该资源
        itypename = i.type.name #该资源的类型
        try:
            if doimg and itypename in ["Texture2D", "Sprite"]:
                #导出图片文件
                data = i.read()
                dest = ospath.join(intodir, data.name)
                dest = ospath.splitext(dest)[0] + ".png"
                if not docover and ospath.isfile(dest):
                    continue
                data.image.save(dest)
                succ = True
            elif dotxt and itypename in ["TextAsset"]:
                #导出文本文件
                data = i.read()
                dest = ospath.join(intodir, data.name)
                if not docover and ospath.isfile(dest):
                    continue
                with open(dest, "wb") as f:
                    f.write(data.script)
                succ = True
            elif doaud and itypename in ["AudioClip"]:
                #导出音频文件
                data = i.read()
                dest = ospath.join(intodir, data.name)
                dest = ospath.splitext(dest)[0] + ".wav"
                if not docover and ospath.isfile(dest):
                    continue
                for n, d in data.samples.items():
                    with open(dest, "wb") as f:
                        f.write(d)
                succ=True
        except Exception as arg:
            #错误反馈
            print(color(1)+"  意外错误：", arg)
            input("  按下回车键以继续任务...\n")
        if succ:
            cont_s += 1
            if detail:
                print(color(6)+"  "+str(i.type.name)+"\t"+str(data.name))
    if detail:
        print(color(2)+"  导出了", cont_s, "个文件"+color(7))
    return cont_s
        

########## Main-主程序 ##########
def main(rootdir:list, destdir:str, dodel:bool=False, 
    doimg:bool=True, dotxt:bool=True, doaud:bool=True, docover:bool=False, detail:bool=True):
    '''
    #### 批量地从指定目录的ab文件中，导出指定类型的资源
    :param rootdir: 包含来源文件夹们的路径的列表;
    :param destdir: 解包目的地的根目录的路径;
    :param dodel:   预先删除目的地文件夹的所有文件，默认False;
    :param doimg:   是否导出图片资源，默认True;
    :param dotxt:   是否导出文本资源，默认True;
    :param doaud:   是否导出音频资源，默认True;
    :param docover: 是否覆盖重名的已存在的文件，默认False，否则可能出现意外;
    :param detail:  是否回显详细信息，默认True，否则回显进度条;
    :returns: (None);
    '''
    print(color(7,0,1)+"\n正在解析目录..."+color(7))
    flist = [] #目录下所有文件的列表
    for i in rootdir:
        flist += get_filelist(i)
    cont_f = 0 #已处理文件计数
    cont_a = 0 #已遍历文件计数
    cont_p = 0 #进度百分比计数
    cont_s_sum = 0 #已导出文件计数（累加）
    if dodel:
        Delete_File_Dir(destdir) #慎用，会预先删除目的地目录的所有内容
    mkdir(destdir)

    if detail:
        print(color(7,0,1)+"开始批量解包!\n"+color(7))
    t1=time.time() #计时器开始

    for i in flist:
        #递归处理各个文件(i是文件的路径名)
        cont_a += 1
        cont_p = round((cont_a/len(flist))*100,1)
        if not os.path.isfile(i):
            continue #跳过目录等非文件路径
        if not os.path.splitext(i)[1] in ['.ab','.AB']:
            continue #跳过非ab文件
        cont_f += 1
        ###
        if detail:
            #显示模式A：流式
            print(color(7))
            print(os.path.dirname(i))
            print('['+os.path.basename(i)+']')
        else:
            #显示模式B：简洁
            os.system('cls')
            print(color(7)+"正在批量解包...")
            print("|"+"■"*int(cont_p//5)+"□"*int(20-cont_p//5)+"|", color(2)+str(cont_p)+"%"+color(7))
            print("当前目录：\t",os.path.dirname(i))
            print("当前文件：\t",os.path.basename(i))
            print("累计解包：\t",cont_f-1)
            print("累计导出：\t",cont_s_sum)
            print()
        ###
        Ue = Upy.load(i) #ab文件实例化
        cont_s_sum += ab_reslove(Ue, os.path.join(destdir, os.path.dirname(i)), doimg, dotxt, doaud, docover, detail)
        ###
        if detail and cont_f % 25 == 0:
            print(color(7,0,1)+"■ 已累计解包",cont_f,"个文件 (",cont_p,"% )")
            print("■ 已累计导出",cont_s_sum,"个文件")

    t2=time.time() #计时器结束
    if not detail:
        os.system('cls')
    print(color(7,0,1)+"\n批量解包结束!")
    print("  累计解包", cont_f, "个文件")
    print("  累计导出", cont_s_sum, "个文件")
    print("  此项用时", round(t2-t1, 1), "秒"+color(7))
    time.sleep(2)