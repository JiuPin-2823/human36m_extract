import glob
import json
import os
import re

import cv2

# 文件目录
src_folder = r'E:\PyCharm\Pose\data\Human36M\archives'  #
out_folder = r'E:\PyCharm\Pose\data\Human36M\images'  #
ann_folder = r'E:\PyCharm\Pose\data\Human36M\annotations'
'''
    archives
     |S1
      |Videos
       |Directions 1.54138969.mp4
       |...
     
    images
     |s_01_act_02_subact_01_ca_01
      |s_01_act_02_subact_01_ca_01_000001.jpg
      |...
'''

# 信息
subject_dict = {'S1': '01', 'S5': '05', 'S6': '06', 'S7': '07', 'S8': '08', 'S9': '09', 'S11': '11'}
camera_dict = {'54138969': '01', '55011271': '02', '58860488': '03', '60457274': '04'}
action_dict = {
    'Directions': '02',
    'Discussion': '03',
    'Eating': '04',
    'Greeting': '05',
    'Phoning': '06',
    'Posing': '07',
    'Purchases': '08',
    'Sitting': '09',
    'SittingDown': '10',
    'Smoking': '11',
    'TakingPhoto': '12',
    'Photo': '12',
    'Waiting': '13',
    'Walking': '14',
    'WalkingDog': '15',
    'WalkDog': '15',
    'WalkTogether': '16'
}

subject_dict_check = {'S1': 'subject1', 'S5': 'subject5', 'S6': 'subject6', 'S7': 'subject7', 'S8': 'subject8', 'S9': 'subject9', 'S11': 'subject11'}


def get_videos(subject_list):
    """
    获取需要处理的视频列表,数据集命名是乱的，先将所有统一命名为01和02，然后利用帧率进行比较
    """

    videos = {}
    for subject in subject_list:
        print(subject)
        path = os.path.join(src_folder, subject, 'Videos')

        videos[subject] = {}
        video_files = glob.glob(os.path.join(src_folder, subject, 'Videos', '*1.54138969.mp4'))  # 只处理1.ca

        with open(os.path.join(ann_folder, 'Human36M_{0}_data.json'.format(subject_dict_check[subject])), 'r') as f:
            content = f.read()

            for video_file in video_files:
                if '_ALL' in video_file:
                    continue
                # 文件夹名称
                target_name_temp = 's_{0}_act_{1}_subact_{2}_ca_01'
                action_str, _, _ = os.path.basename(video_file).split('.')
                action_id = action_dict[action_str.split(' ')[0]]

                for ca in camera_dict:
                    video_1 = os.path.join(path, '{0} 1.{1}.mp4'.format(action_str.split(' ')[0], ca))
                    video_2 = os.path.join(path, '{0} 2.{1}.mp4'.format(action_str.split(' ')[0], ca))
                    this_count_1 = cv2.VideoCapture(video_1).get(cv2.CAP_PROP_FRAME_COUNT)
                    this_count_2 = cv2.VideoCapture(video_2).get(cv2.CAP_PROP_FRAME_COUNT)

                    target_name_1 = 's_{0}_act_{1}_subact_01_ca_{2}'.format(subject_dict[subject], action_id, camera_dict[ca])
                    target_name_2 = 's_{0}_act_{1}_subact_02_ca_{2}'.format(subject_dict[subject], action_id, camera_dict[ca])
                    true_count_1 = len(re.findall(target_name_1 + '_', content))
                    true_count_2 = len(re.findall(target_name_2 + '_', content))

                    if true_count_1 > true_count_2:
                        if this_count_1 > this_count_2:
                            videos[subject][target_name_1] = video_1
                            videos[subject][target_name_2] = video_2
                        else:
                            videos[subject][target_name_1] = video_2
                            videos[subject][target_name_2] = video_1
                    else:
                        if this_count_1 > this_count_2:
                            videos[subject][target_name_1] = video_2
                            videos[subject][target_name_2] = video_1
                        else:
                            videos[subject][target_name_1] = video_1
                            videos[subject][target_name_2] = video_2

    with open('videos.json', 'w') as f:
        f.write(json.dumps(videos))


def extract_video(target_name: str, video_file: str, step: int) -> None:
    """以step为间隔提取视频帧,6位编号，起始为1"""

    path = os.path.join(out_folder, target_name)
    os.makedirs(path, exist_ok=True)
    capture = cv2.VideoCapture(video_file)

    # 开始提取
    index = 1
    if capture.isOpened():
        while True:
            ret, img = capture.read()
            if ret:
                if index % step == 1:
                    # 每step帧取一张,6位编号，取余结果==起始编号
                    filename = target_name + '_' + '%06d' % index + '.jpg'
                    cv2.imwrite(os.path.join(path, filename), img)
                    print("\r{0}: extracted frame: {1}".format(target_name, index), end="")
                index += 1
            else:
                print('')
                break
    else:
        print('open failed:', video_file)
    capture.release()


def check_videos(subject_list):
    with open('videos.json', 'r') as f:
        videos = json.loads(f.read())
    for subject in subject_list:
        with open(os.path.join(ann_folder, 'Human36M_{0}_data.json'.format(subject_dict_check[subject])), 'r') as f:
            content = f.read()
            for video in videos[subject]:
                true_count = len(re.findall(video + '_', content))
                this_count = cv2.VideoCapture(videos[subject][video]).get(cv2.CAP_PROP_FRAME_COUNT)

                if this_count >= true_count:
                    if this_count - true_count > 10:
                        print(this_count - true_count, '\t', videos[subject][video])
                    continue
                else:
                    print(video, this_count, true_count, videos[subject][video])
        print(subject, 'checked')


def check_path():
    with open('path.json', 'r') as f:
        paths = json.loads(f.read())
        paths = [path.replace('..', r'E:\PyCharm\Pose') for path in paths]

        for path in paths:
            if not os.path.exists(path):
                print(path)

if __name__ == '__main__':
    '''单进程太慢，import该代码，同时运行多个窗口'''
    subject_list = ['S1', 'S5', 'S6', 'S7', 'S8', 'S9', 'S11']

    check_path()