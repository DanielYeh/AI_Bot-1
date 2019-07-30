#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Use to generate arm task and run."""

import os
import sys
import copy
from math import degrees

import time
import rospy
from std_msgs.msg import Bool, Int32
from arm_control  import ArmTask, SuctionTask
from yolo_v3.msg  import ROI_array  
from yolo_v3.msg  import ROI  
from comm_stm32   import Gripper

count   = 0
box_cnt = 1

PICKORDER = 0
SPEED_L     = 30

idle            = 0
busy            = 1
initPose        = 2             #(第一個動作)
goto            = 3
down            = 4             #第一段下去
up              = 5
back_home       = 6
wait_img_pos    = 7             #等影像資料
grasping        = 8             #catch
move_standby    = 9             #安全準備位置
box_standby     = 10            #安全準備位置
move_to_box     = 11            #移到箱子上方
box_down        = 12          
box_grasp       = 13            #loosen
box_up          = 14         
move_to_obj     = 15            #移到物品上方
move_to_init    = 16            
down_sec        = 17            #第二段下去
standby_open    = 18            #(第二個動作)準備開抽屜的位置
move_drawer     = 19            #(第三個動作)打開抽屜的位置
catch_drawer    = 20            #開抽屜
loosen_drawer   = 21            #關抽屜
back_pos        = 22
go_safe_point1  = 23            #開完箱子的第一個動作
go_safe_point2  = 24            #開完箱子的第二個動作
go_safe_point3  = 25            #開完箱子的第三個動作
init_grasp      = 26            #夾爪變成 3D_mode
drag_grasp      = 27            #夾爪變成 drag_mode
standby_safe_point = 28         #開完箱子後一到這個中繼點確保安全
close_box_standy = 29           #準備關箱子的位置
close_box_down   = 30           #關箱子
ready_close_box  = 31
box_catch        = 32
close_box_finish = 33           #離開箱子
box_loosen       = 34
back_safe_pose   = 35           
mode_2D_catch    = 36


x = 0
y = 0

class stockingTask:
    def __init__(self, _name = '/robotis'):
        """Initial object."""
        self.en_sim = False
        if len(sys.argv) >= 2:
            print(type(sys.argv[1]))
            if sys.argv[1] == 'True':
                rospy.set_param('self.en_sim', sys.argv[1])
                self.en_sim = rospy.get_param('self.en_sim')
        self.img_data = ROI()
        self.img_data_list = []
        self.name = _name
        self.state = initPose
        self.nowState = initPose 
        self.nextState = idle
        self.reGripCnt = 0
        self.arm = ArmTask(self.name + '_arm')
        self.pos   = [0, 0, 0]
        self.euler = [0, 0, 0]
        self.phi   = 0
        self.sucAngle = 0
        self.No_Object_count = 0
        self.obj_name = ''
        self.standby_safeFlag = True       #  第一次開完箱子的狀態切換（只有開箱子用的到）
        self.close_box = False             #  關箱子的旗標
        self.finish_pos = False
        self.mode_2D = False
        self.finish = False
        if self.name == 'left':
            self.is_right = -1
            self.speed = SPEED_L
            self.faster_speed = 40
        # self.init_pub_sub()
        if self.en_sim:
            self.suction = SuctionTask(self.name + '_gazebo')
        else:
            self.suction = SuctionTask(self.name)
    
    # def init_pub_sub(self):
    #     rospy.Subscriber('/object/ROI_array', ROI_array, self.get_obj_info_cb)

    def process(self):
        if self.arm.is_stop:
            self.finish =  True
            print('!!! Robot is stop !!!')                         
            return  

        if self.state == idle:
            if self.finish:
                return    

        if self.state == busy:
            if self.arm.is_busy:
                return
            else:
                self.state    = self.nextState
                self.nowState = self.nextState
                return  

        #(第一個動作)
        elif self.state == initPose:
            print('self.state == initPose')
            self.state = busy
            #self.nextState = wait_img_pos
            self.arm.set_speed(self.speed)
            self.pos   = [0.4, 0.5, -0.3]
            self.euler = [0, 0, 0]
            self.phi = 0
            self.nextState = move_to_obj
            # self.pos   = [0.48, 0.25, -0.4]
            # self.euler = [0, 0, 0]
            # self.phi = 90
            self.arm.ikMove(mode= 'p2p', pos = self.pos, euler = self.euler, phi = self.phi)  

        # # 夾爪變成 drag_mode
        # elif self.state == drag_grasp:
        #     print('self.state == drag_grasp')
        #     self.state = busy
        #     if self.close_box == False:       #判斷是否為要關箱子
        #         self.nextState = move_drawer
        #     else:
        #         self.nextState = standby_safe_point # 現在在stand by, 到safe_point時有機會繞兩次大圈, 但不會有事
        #     self.arm.clear_cmd()
        #     gripper.Send_Gripper_Command('drag_mode')

        # # 夾爪初始化
        # elif self.state == init_grasp:
        #     print('self.state == init_grasp')
        #     self.state = busy
        #     #self.nextState = wait_img_pos
        #     self.nextState = move_to_obj
        #     self.arm.clear_cmd()
        #     gripper.Send_Gripper_Command('3D_mode')


        # elif self.state == wait_img_pos:        # wait_img_pos
        #     print('self.state == wait_img_pos')
        #     self.state = wait_img_pos
        #     # print('len(self.img_data_list = ', len(self.img_data_list))
        #     #print('aaaaa')
        #     #rospy.Subscriber('/object/ROI_array', ROI_array, self.get_obj_info_cb)

        #     #if(len(self.img_data_list)!=0):
        #     #print("str(self.img_data.object_name): ", str(self.img_data.object_name))

        #     if(len(self.img_data_list)!=0):
        #         #print('bbbb')
        #         self.No_Object_count = 0
        #         for i in range(len(self.img_data_list)):
        #             # if(i!=0):
        #             #     print("\n")
        #             if (self.img_data.min_x > 638) and (self.img_data.min_y > 156) and (self.img_data.Max_x < 1188) and (self.img_data.Max_y < 811):        
        #                 print("----- stra detect object_" + str(i) + " ----- ")
        #                 print("object_name = " + str(self.img_data.object_name))
        #                 print("score = " + str(self.img_data.score))
        #                 print("min_xy = [ " +  str( [self.img_data.min_x, self.img_data.min_y] ) +  " ]" )
        #                 print("max_xy = [ " +  str( [self.img_data.Max_x, self.img_data.Max_y] ) +  " ]" )
        #                 self.nextState = goto
        #                 self.obj_name = self.img_data.object_name
        #                 x = (self.img_data.min_x + self.img_data.Max_x)/2
        #                 y = (self.img_data.min_y + self.img_data.Max_y)/2    
        #                 time.sleep(1)
        #             else:
        #                 print('object over range!!')
        #     else:
        #         print('no object!!!')
        #         self.nextState = wait_img_pos
        #         self.No_Object_count += 1
        #     self.state = self.nextState  
        #     if self.No_Object_count == 500:      #判斷桌上是否沒有物件
        #         self.state = move_standby
        #         self.close_box = True                          

        # # 防止影像狀態機怪怪的空狀態(必定接在wait_img_pos後面)
        # elif self.state == goto:              
        #     print('self.state == goto')
        #     self.state = busy
        #     if self.standby_safeFlag == True:
        #         self.nextState = standby_safe_point
        #     else:
        #         self.nextState = move_standby
        

        elif self.state == move_to_obj:          
            global x
            global y

            print('self.state == move_to_obj')
            self.arm.set_speed(self.speed)
            
            # posX , posY = self.Image_transform(x, y)

            self.state = busy
            self.nextState = down
            # self.pos   = [round(posX, 4), round(posY, 4), -0.45]
            self.pos   = [0.3, 0.4, -0.45]
            print(self.pos)
            self.euler = [0, 0, 0]
            self.phi = 0
            self.arm.ikMove(mode= 'p2p', pos = self.pos, euler = self.euler, phi = self.phi)    

        elif self.state == down:               # down
            print('self.state == down')
            self.arm.set_speed(self.faster_speed)
            self.state = busy
            self.nextState = down_sec
            self.pos   = [0, 0, -0.1]
            self.arm.relative_move_pose(mode='p2p', pos=self.pos)
            rospy.sleep(.1)

        elif self.state == down_sec:
            print('self.state == down_sec')
            self.arm.set_speed(self.speed)
            self.state = busy
            self.nextState = up  
            self.pos  = [0, 0, -0.1]
            self.arm.relative_move_pose(mode='p2p', pos=self.pos)

        # elif self.state == grasping:
        #     print('self.state == ready to grasping')
        #     self.arm.clear_cmd()
        #     self.state = busy
        #     if self.mode_2D == True:
        #         gripper.Send_Gripper_Command('2D_catch')
        #     else:
        #         gripper.Send_Gripper_Command('Catch_all')
        #     self.nextState = up
                

        elif self.state == up:               # up
            print('self.state == up')
            self.arm.set_speed(self.faster_speed)
            self.state = busy
            self.nextState = initPose
            self.pos   = [0, 0, 0.2]
            self.arm.relative_move_pose(mode='p2p', pos=self.pos)  

        # # 就是stand_by, 跟stand by狀態完全一樣
        # elif self.state == box_standby:
        #     print('self.state == box_standby')
        #     self.arm.set_speed(self.speed)
        #     self.state = busy
        #     self.nextState = move_to_box  
        #     self.pos   = [0, 0.5, -0.4]
        #     self.euler = [0, 0, 0]
        #     self.phi = 0
        #     self.arm.ikMove(mode = 'p2p', pos = self.pos, euler = self.euler, phi = self.phi)          

    #-------------------------座標轉換------------------------------------------------------
    def Image_transform(self, Camera_Image_X, Camera_Image_Y):
        Arm_posX = (866 - Camera_Image_Y)*0.000889 - 0.4795     
        Arm_posY = (974 - Camera_Image_X)*0.000889 + 0.3960     
        return Arm_posX, Arm_posY


    #-------------------------------------------------------------------------------
    def get_obj_info_cb(self, data):
        self.img_data = ROI()
        self.img_data_list = data.ROI_list
        #print("Detected object number = " + str(len(data.ROI_list)))
        for i in range(len(data.ROI_list)):
            #if (data.ROI_list[i].min_x > 400) and (data.ROI_list[i].min_y) > 20 and (data.ROI_list[i].Max_x < 1440) and (data.ROI_list[i].Max_y < 990):
            self.img_data.object_name = data.ROI_list[i].object_name
            self.img_data.score       = data.ROI_list[i].score
            self.img_data.min_x = data.ROI_list[i].min_x
            self.img_data.min_y = data.ROI_list[i].min_y
            self.img_data.Max_x = data.ROI_list[i].Max_x
            self.img_data.Max_y = data.ROI_list[i].Max_y
            return self.img_data


if __name__ == '__main__':
    rospy.init_node('gripperasd', anonymous=True)
    # gripper = Gripper()
    # gripper.Send_Gripper_Command('3D_mode')     # required for gripper initial
    # gripper.Send_Gripper_Command('Catch_all')
    # gripper.Send_Gripper_Command('rot_to_norm')
    
    left  = stockingTask('left')       # Set up left arm controller
    rospy.sleep(.3)

    rate = rospy.Rate(50)

    while not rospy.is_shutdown():
        try:
            left.process()
        except rospy.ROSInterruptException:
            print('error')
            pass
            break
        rate.sleep()
