#bilibili_live_spider,created on 2021.02.24

from selenium import webdriver, common
from selenium.webdriver.chrome.options import Options
from multiprocessing.dummy import Pool
from lxml import etree
from time import sleep, time
import os
import csv


# 弹幕，礼物读取函数
def get_list(bro):
    tree = etree.HTML(bro.page_source)
    #分别为uid，标示值，弹幕，发送礼物用户，礼物名称，礼物数目
    uid_list = tree.xpath('//div[@class = "chat-item danmaku-item "]/@data-uid')
    ct_list = tree.xpath('//div[@class = "chat-item danmaku-item "]/@data-ct')
    danmaku_list = tree.xpath('//div[@class = "chat-item danmaku-item "]/@data-danmaku')
    gift_uname_list = tree.xpath('//span[@class = "username v-bottom"]/text()')
    gift_name_list = tree.xpath('//span[@class = "gift-name v-bottom"]/text()')
    gift_count_list = tree.xpath('//span[@class = "gift-total-count v-bottom"]/text()')
    return uid_list, ct_list, danmaku_list, gift_uname_list, gift_name_list, gift_count_list


# 去重函数
def remove_repeat(seq):
    once = seq[0]
    total = seq[1]
    try:
        cut_index = once.index(total[-1])
        once = once[cut_index + 1 :]
        total.extend(once)
    except ValueError:
        total.extend(once)


# 清屏函数
def clear():
    os.system('cls')


# -----------------------提示用户输入部分--------------------------

# 初始化总列表，第一个包含了与弹幕有关的所有列表，第二个包含了与礼物有关的所有列表
total_danmaku_list = ['_']   # 占位符
total_gift_list = ['_']

url = input('请输入bilibili直播间地址：')
mode = input('选择模式，输入slow或fast。slow适用于600万以内人数直播间，fast适用于多于600万人数直播间')
# 算法设计上有一个元素用于占位比较，所以201实际有效数量只有200个
if mode == 'slow':
    temp_num = 201
    refresh_time = 1
elif mode == 'fast':
    temp_num = 401
    refresh_time = 0.5
else:
    temp_num = 201
    refresh_time = 1
    print('模式错误，已默认设为slow模式！')

# 选择监视选项
monitoring = input('选择在屏幕上输出以监视的是弹幕还是礼物信息。（弹幕输入d，礼物信息输入g）')
if monitoring == 'd':
    command = r'print(total_danmaku_list)'
elif monitoring == 'g':
    command = r'print(total_gift_list)'
else:
    command = r'print(total_danmaku_list)'
    print('模式错误，已默认设置为弹幕监视！')

# 选择路径
work_path = input('输入爬取数据保存的文件路径：（运行完成后文件存为danmaku.csv和gift.csv）')
if os.path.exists(work_path):
    os.chdir(work_path)
else:
    os.makedirs(work_path)
    os.chdir(work_path)

# 指定运行时间
run_time = int(input('输入运行时长，（单位：秒数，若需要运行至直播间关闭，请输入0）'))
# 因为后面默认检测运行时长和直播间是否关闭的信号，所以设置48h时长，这样一般就只有直播间关闭才能退出了
if run_time == 0:
    run_time = 172800
elif run_time > 0:
    pass
else:
    run_time = 172800
    print('不能为负数，已默认选择执行至直播间关闭！')

# -----------------------正式运行部分--------------------------

# 初始化浏览器对象，同时设置为无UI模式
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable--gpu')
bro = webdriver.Chrome('C:/Users/15742/chromedriver.exe', chrome_options = chrome_options)

# 创建弹幕和礼物csv管道，同时写入表格标题
fp_danmaku = open(r'./danmaku.csv', 'a', encoding = 'utf-8_sig', newline = '')
fp_gift = open(r'./gift.csv', 'a', encoding = 'utf-8_sig', newline = '')
danmaku_writer = csv.writer(fp_danmaku)
gift_writer = csv.writer(fp_gift)
csv_danmaku_headers = ['ct_list', 'uid_list', 'danmaku_list']
csv_gift_headers = ['gift_uname_list', 'gift_name_list', 'gift_count_list']
danmaku_writer.writerow(csv_danmaku_headers)
gift_writer.writerow(csv_gift_headers)

# 定位iframe，有iframe则切换
bro.get(url)
sleep(1)
try:
    iframe_tag = bro.find_element_by_xpath('//div[@class = "player"]//iframe')
    bro.switch_to.frame(iframe_tag)
except common.exceptions.NoSuchElementException:
    pass

# 起始计时标记
start_time = time()

while True:
    # 获取，填入总列表
    uid_list, ct_list, danmaku_list, gift_uname_list, gift_name_list, gift_count_list = get_list(bro)
    once_danmaku_list = list(zip(ct_list, uid_list, danmaku_list))
    once_gift_list = list(zip(gift_uname_list, gift_name_list, gift_count_list))

    #设置两个线程分别对两个总列表去重
    pool = Pool(2)
    arg_list = [(once_danmaku_list, total_danmaku_list), (once_gift_list, total_gift_list)]
    pool.map(remove_repeat, arg_list)

    # 一次循环清一次屏，再重新输出，避免大量输出堆积占用内存
    clear()
    eval(command)

    # 判断弹幕信息是否多于最大缓存量，是则写入csv一次，并清空总列表，以降低内存压力
    if len(total_danmaku_list) >= temp_num:
        del total_danmaku_list[0]
        danmaku_writer.writerows(total_danmaku_list)
        print('\n------>弹幕进行了一次保存\n')
        total_danmaku_list = [total_danmaku_list[-1]]

    # 判断礼物信息是否多于最大缓存量，是则写入csv一次，并清空总列表，以降低内存压力
    if len(total_gift_list) >= temp_num:
        del total_gift_list[0]
        gift_writer.writerows(total_gift_list)
        print('\n------>礼物信息进行了一次保存\n')
        total_gift_list = [total_gift_list[-1]]

    # 检查是否达到运行时长，暂存在列表中的数据也写入
    check_time = time()
    if check_time - start_time > run_time:
        print('运行时长已到，等待程序结束中...')
        del total_danmaku_list[0]
        del total_gift_list[0]
        danmaku_writer.writerows(total_danmaku_list)
        gift_writer.writerows(total_gift_list)
        break

    # 检查直播间是否关闭，暂存在列表中的数据也写入
    try:
        bro.find_element_by_xpath('//div[@ class = "bilibili-live-player-ending-panel-info"]')
        print('直播间已关闭，等待程序结束中...')
        del total_danmaku_list[0]
        del total_gift_list[0]
        danmaku_writer.writerows(total_danmaku_list)
        gift_writer.writerows(total_gift_list)
        break
    except common.exceptions.NoSuchElementException:
        pass

    # 刷新的频率
    sleep(refresh_time)

# 退出浏览器对象，留一定时间给用户阅读反馈信息
bro.quit()
print('\n------>运行完成\n')
sleep(5)
