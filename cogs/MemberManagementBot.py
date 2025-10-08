import os
import typing
import asyncio
import enum
import json
import datetime
import re

from emoji import is_emoji

import discord
from discord.ext import commands
from discord.ext import tasks

#import main

# Cog内で使用するソースフォルダのパス
SOURCE = os.path.join(os.environ['SOURCE'],os.path.basename(__file__).removesuffix('.py'))

BOT : discord.Client



COURSE = typing.Literal[
    'none',
    'class5',
    'class6',
    'class7',
    'class8',
    'courseT',
    'courseR',
    'courseA',
    'courseW',
]

GRADE = typing.Literal[
    'none',
    'grade1',
    'grade2',
    'grade3',
    'grade4',
    'grade5',
    'special',
    'graduation',
]

RANK = typing.Literal[
    'visitor',
    'member',
    'staff',
    'admin',
    'retirement',
    'consultant',
    'owner',
]

GRADE0 = [
    {
        'name' : '1年生',
        'value' : 'grade1'
    },
    {
        'name' : '2年生',
        'value' : 'grade2'
    },
    {
        'name' : '3年生',
        'value' : 'grade3'
    },
    {
        'name' : '4年生',
        'value' : 'grade4'
    },
    {
        'name' : '5年生',
        'value' : 'grade5'
    },
    {
        'name' : '専攻科',
        'value' : 'special'
    },
    {
        'name' : '卒業生',
        'value' : 'graduation'
    },
]

GRADE_DICT = {
    'grade1' : '1年生',
    'grade2' : '2年生',
    'grade3' : '3年生',
    'grade4' : '4年生',
    'grade5' : '5年生',
    'special' : '専攻科',
    'graduation' : '卒業生'
}

COURSE_DICT = {
    'courseT' : '情報通信工学コース',
    'courseR' : 'ロボット工学コース',
    'courseA' : '航空宇宙工学コース',
    'courseW' : '医療福祉工学コース',
    'class5' : '1-5',
    'class6' : '1-6',
    'class7' : '1-7',
    'class8' : '1-8'
}

RANK_DICT = {
    'visitor' : '見学',
    'member' : '会員',
    'staff' : '幹部',
    'admin' : '会長',
    'retirement' : '卒業生',
    'consultant' : '顧問',
    'owner' : '管理者'
}

start_time = 20040401


class InputError(Exception):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}の値が不正です'
        pass




class memberData(typing.TypedDict):
    name       : str
    rank       : RANK
    grade      : GRADE
    course     : COURSE
    interest  : typing.List[str]
    stop_count : int

class roleData(typing.TypedDict):
    type         : str
    name         : str
    value        : str
    display_name : str

class roleTagData(typing.TypedDict):
    name         : str
    role_id      : int
    display_name : str
    value        : str

class roleType(typing.TypedDict):
    rank : typing.Dict[str,roleTagData]
    grade: typing.Dict[str,roleTagData]
    course : typing.Dict[str,roleTagData]
    interest : typing.Dict[str,roleTagData]

class channelData(typing.TypedDict):
    channel : int
    message : int

class interestData(typing.TypedDict):
    label : str
    emoji : str
    role_id : int
    channel_id : int


class GuildData:
    parameters : typing.Dict[str,typing.Any]   = {}
    members    : typing.Dict[str,memberData]   = {}
    roles      : typing.Dict[str,roleData]     = {}
    channels   : typing.Dict[str,channelData]  = {}
    interests  : typing.Dict[str,interestData] = {}

    role_tags  : typing.Dict[str,roleTagData] = {}
    
    source     : str

    def __init__(self,guild_id:int):
        self.guild_id = str(guild_id)

        self.source = os.path.join(os.environ['SOURCE'],self.guild_id)

        os.makedirs(self.source, exist_ok=True)

        if not os.path.exists(os.path.join(self.source,'parameters.json')):
            self.parameters = {}
        else:
            with open(os.path.join(self.source,'parameters.json'),encoding='utf-8') as f:
                self.parameters = json.load(f)
        
        if not os.path.exists(os.path.join(self.source,'memberList.json')):
            self.members = {}
        else:
            with open(os.path.join(self.source,'memberList.json'),encoding='utf-8') as f:
                self.members = json.load(f)

        if not os.path.exists(os.path.join(self.source,'roleList.json')):
            self.roles = {}
        else:
            with open(os.path.join(self.source,'roleList.json'),encoding='utf-8') as f:
                self.roles = json.load(f)
            
        if not os.path.exists(os.path.join(self.source,'channelList.json')):
            self.channels = {}
        else:
            with open(os.path.join(self.source,'channelList.json'),encoding='utf-8') as f:
                self.channels = json.load(f)

        if not os.path.exists(os.path.join(self.source,'interestList.json')):
            self.interests = {}
        else:
            with open(os.path.join(self.source,'interestList.json'),encoding='utf-8') as f:
                self.interests = json.load(f)
        pass

    def save_member_data(self):
        with open(os.path.join(self.source,'memberList.json'),'w',encoding='utf-8') as f:
            json.dump(self.members,f,indent=4,ensure_ascii=False)
        pass

    def save_role_data(self):
        with open(os.path.join(self.source,'roleList.json'),'w',encoding='utf-8') as f:
            json.dump(self.roles,f,indent=4,ensure_ascii=False)
        pass

    def save_channel_data(self):
        with open(os.path.join(self.source,'channelList.json'),'w',encoding='utf-8') as f:
            json.dump(self.channels,f,indent=4,ensure_ascii=False)
        pass

    def save_interest_data(self):
        with open(os.path.join(self.source,'interestList.json'),'w',encoding='utf-8') as f:
            json.dump(self.interests,f,indent=4,ensure_ascii=False)
        pass

    def save_parameters(self):
        with open(os.path.join(self.source,'parameters.json'),'w',encoding='utf-8') as f:
            json.dump(self.parameters,f,indent=4,ensure_ascii=False)
        pass



class MemberManagerBot(commands.Cog):
    # ウィジェット
    class JoinWidget:
        class Start(dict):
            class Embed(discord.Embed):
                def __init__(self):
                    super().__init__(
                        title = '入会手続き',
                        description = 'ボタンを押して仮入会手続きを開始します',
                        color = 0x8866cc
                    )

            class View(discord.ui.View):
                def __init__(self):
                    super().__init__()
                    self.add_item(
                        discord.ui.Button(
                            label = '参加申請',
                            style = discord.ButtonStyle.primary,
                            custom_id = 'media_mgt_join'
                        )
                    )

            def __init__(self):
                self['embed'] = self.Embed()
                self['view'] = self.View()

        class Main(dict):
            class Embed(discord.Embed):
                def __init__(self,grade:str,course:str):
                    self.grade = {g['value']:g['name'] for g in GRADE0}.get(grade,'--')
                    self.course = ({'courseT':'情報通信工学コース','courseW':'医療福祉工学コース','courseR':'ロボット工学コース','courseA':'航空宇宙工学コース'} if grade != 'grade1' else {'class5':'1-5','class6':'1-6','class7':'1-7','class8':'1-8'}).get(course,'--')

                    super().__init__(
                        title = '参加申請',
                        description = '```ansi\n'\
                            f'学  年：{self.grade}\n'\
                            f'コース：{self.course}\n'\
                            '```',
                        color = 0x8866cc
                    )
                pass

            class View(discord.ui.View):
                flag = False
                class Modal(discord.ui.Modal):
                    def __init__(self,grade:str,course:str):
                        super().__init__(
                            title = '参加申請'
                        )

                        self.grade = grade
                        self.course = course

                        self.item = discord.ui.TextInput(
                            label = '名前',
                            placeholder = '名前を入力してください。',
                            custom_id = 'name',
                            style = discord.TextStyle.short
                        )

                        self.add_item(self.item)


                    async def on_submit(self,interaction:discord.Interaction):
                        await interaction.response.defer(thinking=False,ephemeral=True)

                        flag = await MemberManagerBot.set_member_data(interaction.user,{
                            'name' : self.item.value,
                            'rank' : 'visitor',
                            'grade' : self.grade,
                            'course' : self.course
                        })

                        if flag:
                            await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.JoinWidget.End(self.item.value,self.grade,self.course))
                        else:
                            await interaction.followup.edit_message(interaction.message.id,content='入会手続きに失敗しました')

                        await asyncio.sleep(10)
                        await interaction.followup.delete_message(interaction.message.id)


                def __init__(self,grade:str,course:str):
                    super().__init__()
                    self.grade = grade
                    self.course = course if course is not None else ''

                    gradeDict = {
                        'grade1':'1年生',
                        'grade2':'2年生',
                        'grade3':'3年生',
                        'grade4':'4年生',
                        'grade5':'5年生',
                        'special':'専攻科生',
                    }
                    courseDict = {
                        'class5':'1-5',
                        'class6':'1-6',
                        'class7':'1-7',
                        'class8':'1-8',
                        'courseT':'情報通信工学コース',
                        'courseR':'ロボット工学コース',
                        'courseW':'医療福祉工学コース',
                        'courseA':'航空宇宙工学コース'
                    }

                    item = discord.ui.Select(
                        placeholder='学年を選択してください',
                        min_values=1,
                        max_values=1,
                        options=[
                            discord.SelectOption(label=value,value=key,default=key == grade) for key,value in gradeDict.items()
                        ]
                    )
                    item.callback = self.grade_select

                    self.add_item(item)

                    item = discord.ui.Select(
                        placeholder='コースを選択してください',
                        min_values=1,
                        max_values=1,
                        options=[
                            discord.SelectOption(label=value,value=key,default=key == course) for key,value in courseDict.items() if (key.startswith('class') if grade == 'grade1' else key.startswith('course'))
                        ],
                        disabled= grade not in gradeDict.keys(),
                    )
                    item.callback = self.course_select

                    self.add_item(item)

                    item = discord.ui.Button(
                        label = '進む',
                        style = discord.ButtonStyle.primary,
                        disabled =not(course.startswith('class') if grade == 'grade1' else self.course.startswith('course') and grade in gradeDict.keys()),
                    )
                    item.callback = self.next

                    self.add_item(item)


                async def grade_select(self,interaction:discord.Interaction):
                    await interaction.response.defer(thinking=False,ephemeral=True)
                    if self.flag:return
                    self.flag = True

                    await interaction.followup.edit_message(interaction.message.id,
                        **MemberManagerBot.JoinWidget.Main(interaction.data['values'][0],self.course)
                    )
                    try:
                        await asyncio.sleep(3600)
                        await interaction.followup.delete_message(interaction.message.id)
                    except:
                        pass

                async def course_select(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.defer(thinking=False,ephemeral=True)
                    await interaction.followup.edit_message(interaction.message.id,
                        **MemberManagerBot.JoinWidget.Main(self.grade,interaction.data['values'][0])
                    )
                    try:
                        await asyncio.sleep(3600)
                        await interaction.followup.delete_message(interaction.message.id)
                    except:
                        pass

                async def next(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.send_modal(
                        self.Modal(self.grade,self.course)
                    )


            def __init__(self,grade = None, course = None):
                self['content'] = '💡:使い方がわからない、正常に動作しない時は質問して下さい'
                self['embed'] = self.Embed(grade,course)
                self['view'] = self.View(grade,course)

        class End(dict):
            class Embed(discord.Embed):
                def __init__(self,name:str,grade:str,course:str):
                    self.grade = {g['value']:g['name'] for g in GRADE0}.get(grade,'--')
                    self.course = ({'courseT':'情報通信工学コース','courseW':'医療福祉工学コース','courseR':'ロボット工学コース','courseA':'航空宇宙工学コース'} if grade != 'grade1' else {'class5':'1-5','class6':'1-6','class7':'1-7','class8':'1-8'}).get(course,'--')


                    super().__init__(
                        title = '入会手続きが完了しました',
                        description = '```ansi\n'\
                            f'名  前：{name}\n'\
                            f'学  年：{self.grade}\n'\
                            f'コース：{self.course}\n'\
                            '```',
                        color = 0x8866cc
                    )
                pass

            def __init__(self,name,grade,course):
                self['content'] = None
                self['embed'] = self.Embed(name,grade,course)
                self['view'] = None


    class UpdateWidget:
        class Start(dict):
            class Embed(discord.Embed):
                def __init__(self):
                    super().__init__(
                        title = '更新手続き',
                        description = '新学期に伴う更新手続きを行います',
                        color = 0x8866cc
                    )
                pass

            class View(discord.ui.View):
                def __init__(self):
                    super().__init__()
                    self.add_item(
                        discord.ui.Button(
                            label = '開始',
                            style = discord.ButtonStyle.primary,
                            custom_id = 'media_mgt_update'
                        )
                    )
                pass

            def __init__(self):
                self['embed'] = self.Embed()
                self['view'] = self.View()

        class Main(dict):
            class Embed(discord.Embed):
                def __init__(self,member:memberData,grade:str,course:str):
                    self.member = member
                    self.grade = GRADE_DICT.get(grade,'--')
                    self.course = COURSE_DICT.get(course,'--')
                    self.course = '--' if (grade == 'grade1' and course.startswith('course')) or (grade != 'grade1' and course.startswith('class')) else self.course

                    if (self.member.get('stop_count',0) > 1):
                        super().__init__(
                            title = '更新情報',
                            description = '```ansi\n'\
                                f'学  年：{GRADE_DICT.get(self.member["grade"],"--")} -> {self.grade}\n'\
                                f'コース：{COURSE_DICT.get(self.member["course"],"--")} -> {self.course}\n'\
                                '```',
                            color = 0x8866cc
                        )
                    else:
                        super().__init__(
                            title = '更新情報',
                            description = '```ansi\n'\
                                f'学  年：{self.grade}\n'\
                                f'コース：{self.course}\n'\
                                '```',
                            color = 0x8866cc
                        )
                pass

            class View(discord.ui.View):
                flag = False

                def __init__(self,member:memberData,grade:str,course:str):
                    super().__init__()
                    self.member = member
                    self.grade = grade if grade is not None else self.member['grade']
                    self.course = course if course is not None else self.member['course']

                    gradeDict = {
                        'grade1':'1年生',
                        'grade2':'2年生',
                        'grade3':'3年生',
                        'grade4':'4年生',
                        'grade5':'5年生',
                        'special':'専攻科生',
                        'graduation':'卒業生'
                    }
                    courseDict = {
                        'class5':'1-5',
                        'class6':'1-6',
                        'class7':'1-7',
                        'class8':'1-8',
                        'courseT':'情報通信工学コース',
                        'courseR':'ロボット工学コース',
                        'courseW':'医療福祉工学コース',
                        'courseA':'航空宇宙工学コース'
                    }

                    if (self.member['stop_count'] > 1):
                        n = list(gradeDict.keys()).index(self.member['grade'])

                        self.grade_select = discord.ui.Select(
                            placeholder='学年を選択してください',
                            min_values=1,
                            max_values=1,
                            options=[
                                discord.SelectOption(label=GRADE0[i]['name'],value=GRADE0[i]['value'],default=(GRADE0[i]['value'] == self.grade)) for i in range(n,min(n+self.member['stop_count'],6)+1)
                            ]
                        )
                        self.grade_select.callback = self.on_grade_select
                        self.add_item(self.grade_select)



                        self.course_select = discord.ui.Select(
                            placeholder='コースを選択してください',
                            min_values=1,
                            max_values=1,
                            options=[
                                discord.SelectOption(label=value,value=key,default=key == (self.member['course'] if self.grade == 'grade1' else self.course)) for key,value in courseDict.items() if (key.startswith('class') if (self.grade == 'grade1') else key.startswith('course'))
                            ],
                            disabled= not(self.member['grade'] == 'grade1' and self.grade != 'grade1')
                        )
                        self.course_select.callback = self.on_course_select
                        self.add_item(self.course_select)

                        self.course = self.member['course'] if not((self.grade == 'grade1' and self.course.startswith('class')) or (self.grade != 'grade1' and self.course.startswith('course'))) else self.course
                        item = discord.ui.Button(
                            label = '進む',
                            style = discord.ButtonStyle.primary,
                            disabled =not(self.course.startswith('class') if self.grade == 'grade1' else self.course.startswith('course') and self.grade in gradeDict.keys()),
                        )
                        item.callback = self.on_next

                        self.add_item(item)

                    else:
                        self.course_select = discord.ui.Select(
                            placeholder='コースを選択してください',
                            min_values=1,
                            max_values=1,
                            options=[
                                discord.SelectOption(label=value,value=key,default=key == (self.course)) for key,value in courseDict.items() if (key.startswith('course'))
                            ],
                            disabled= not(self.member['grade'] == 'grade1')
                        )
                        self.course_select.callback = self.on_course_select
                        self.add_item(self.course_select)


                        item = discord.ui.Button(
                            label = '卒業',
                            style = discord.ButtonStyle.primary,
                            disabled =self.member['grade'] not in ['grade5','special','graduation'],
                        )
                        item.callback = self.on_graduation

                        self.add_item(item)


                        item = discord.ui.Button(
                            label = '進級',
                            style = discord.ButtonStyle.green,
                            disabled = (self.member['grade'] in ['special','graduation']) or (self.grade == 'grade1' and self.course.startswith('class')),
                        )
                        item.callback = self.on_promotion

                        self.add_item(item)


                        item = discord.ui.Button(
                            label = '留年',
                            style = discord.ButtonStyle.red,
                            disabled = False
                        )
                        item.callback = self.on_retention

                        self.add_item(item)


                async def on_grade_select(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.defer(thinking=False,ephemeral=True)
                    await interaction.followup.edit_message(interaction.message.id,
                        **MemberManagerBot.UpdateWidget.Main(self.member,interaction.data['values'][0],self.course)
                    )
                    try:
                        await asyncio.sleep(3600)
                        await interaction.followup.delete_message(interaction.message.id)
                    except:
                        pass

                async def on_course_select(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.defer(thinking=False,ephemeral=True)
                    await interaction.followup.edit_message(interaction.message.id,
                        **MemberManagerBot.UpdateWidget.Main(self.member,self.grade,interaction.data['values'][0])
                    )
                    try:
                        await asyncio.sleep(3600)
                        await interaction.followup.delete_message(interaction.message.id)
                    except:
                        pass

                async def on_next(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await self.finish(interaction)

                async def on_graduation(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    self.grade = 'graduation'
                    await self.finish(interaction)

                async def on_promotion(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    if self.member['grade'] == 'grade1':self.grade = 'grade2'
                    elif self.member['grade'] == 'grade2':self.grade = 'grade3'
                    elif self.member['grade'] == 'grade3':self.grade = 'grade4'
                    elif self.member['grade'] == 'grade4':self.grade = 'grade5'
                    elif self.member['grade'] == 'grade5':self.grade = 'special'
                    elif self.member['grade'] == 'special':self.grade = 'graduation'

                    await self.finish(interaction)

                async def on_retention(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    self.course = self.member['course']
                    await self.finish(interaction)

                async def finish(self,interaction:discord.Interaction):
                    await interaction.response.defer(thinking=False,ephemeral=True)
                    await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.UpdateWidget.End(self.member,self.grade,self.course))
                    data = self.member.copy()
                    data['grade'] = self.grade
                    data['course'] = self.course
                    data['stop_count'] = 0
                    await MemberManagerBot.set_member_data(interaction.user,data)
                    await asyncio.sleep(10)
                    await interaction.followup.delete_message(interaction.message.id)

            def __init__(self,member,grade = None, course = None):
                grade = grade if grade is not None else member['grade']
                course = course if course is not None else member['course']
                self['content'] = '💡:使い方がわからない、正常に動作しない時は質問して下さい'
                self['embed'] = self.Embed(member,grade,(course if(course.startswith('class'))else member['course']) if grade=='grade1' else (course if(course.startswith('course'))else member['course']))
                self['view'] = self.View(member,grade,course)

        class End(dict):
            class Embed(discord.Embed):
                def __init__(self,member:memberData,grade:str,course:str):
                    self.member = member
                    self.grade = {g['value']:g['name'] for g in GRADE0}.get(grade,'--')
                    self.course = ({'courseT':'情報通信工学コース','courseW':'医療福祉工学コース','courseR':'ロボット工学コース','courseA':'航空宇宙工学コース'} if grade != 'grade1' else {'class5':'1-5','class6':'1-6','class7':'1-7','class8':'1-8'}).get(course,'--')

                    gr = {g['value']:g['name'] for g in GRADE0}.get(self.member['grade'],'--')
                    co = {'courseT':'情報通信工学コース','courseW':'医療福祉工学コース','courseR':'ロボット工学コース','courseA':'航空宇宙工学コース','class5':'1-5','class6':'1-6','class7':'1-7','class8':'1-8'}.get(self.member['course'],'--')



                    super().__init__(
                        title = '更新手続きが完了しました',
                        description = '```ansi\n'\
                            f'名　前：{self.member["name"]}\n'\
                            f'学　年：{gr}'+ (f' -> {self.grade}' if self.grade != self.member['grade'] else '') + '\n'\
                            f'コース：{co}' + (f' -> {self.course}' if self.course != self.member['course'] else '') + '\n'\
                            '```',
                        color = 0x8866cc
                    )
                pass

            def __init__(self,member,grade,course):
                self['content'] = None
                self['embed'] = self.Embed(member,grade,course)
                self['view'] = None


    class InterestWidget:
        class Start(dict):
            class Embed(discord.Embed):
                def __init__(self):
                    super().__init__(
                        title = '所属班設定',
                        description = '所属する班を設定します',
                        color = 0x8866cc
                    )

                    self.add_field(name='班一覧',value='\n'.join([f'{v["emoji"]}：{v["label"]}' for k,v in MemberManagerBot.interestList.items()]))
                pass

            class View(discord.ui.View):
                def __init__(self):
                    super().__init__()
                    self.add_item(
                        discord.ui.Button(
                            label = '開始',
                            style = discord.ButtonStyle.primary,
                            custom_id = 'media_mgt_interest'
                        )
                    )
                pass

            def __init__(self):
                self['embed'] = self.Embed()
                self['view'] = self.View()

        class Main(dict):
            class Embed(discord.Embed):
                def __init__(self,mem:memberData):
                    super().__init__(
                        title = '現在の所属班',
                        description = '\n'.join([f'{MemberManagerBot.interestList[i]["emoji"]}:{MemberManagerBot.interestList[i]["label"]}' for i in mem.get('interest',[]) if i in MemberManagerBot.interestList.keys()]),
                        color = 0x8866cc
                    )


            class View(discord.ui.View):
                flag = False
                def __init__(self,mem:memberData,interest:typing.List[str]):
                    super().__init__()
                    self.mem = mem
                    self.interest = interest
                    for key,value in MemberManagerBot.interestList.items():
                        btn = discord.ui.Button(
                            style = discord.ButtonStyle.green if (key in self.interest) else discord.ButtonStyle.grey,
                            custom_id = key,
                            emoji = value['emoji']
                        )
                        btn.callback = self.on_interest
                        self.add_item(btn)

                    self.button_enter = discord.ui.Button(
                        label = '完了',
                        style = discord.ButtonStyle.primary,
                        row=4
                    )
                    self.button_enter.callback = self.on_enter
                    self.add_item(self.button_enter)

                async def on_interest(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.defer(thinking=False,ephemeral=True)

                    data = MemberManagerBot.interestList.get(interaction.data.get('custom_id',''))
                    if data is not None:
                        if interaction.data.get('custom_id','') in self.interest:
                            self.interest.remove(interaction.data.get('custom_id',''))
                        else:
                            self.interest.append(interaction.data.get('custom_id',''))

                    await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.InterestWidget.Main(self.mem,self.interest))

                    try:
                        await asyncio.sleep(3600)
                        await interaction.followup.delete_message(interaction.message.id)
                    except:
                        pass

                async def on_enter(self,interaction:discord.Interaction):
                    if self.flag:return
                    self.flag = True
                    await interaction.response.defer(thinking=False,ephemeral=True)

                    data = self.mem.copy()
                    data['interest'] = self.interest

                    await MemberManagerBot.set_member_data(interaction.user,data)
                    await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.InterestWidget.End())

                    await interaction.followup.delete_message(interaction.message.id)



            def __init__(self,mem:memberData,interest:typing.List[str]=None):
                if interest is  None:
                    interest = mem.get('interest',[]).copy()
                self['content'] = '💡:使い方がわからない、正常に動作しない時は質問して下さい'
                self['embed'] = self.Embed(mem)
                self['view'] = self.View(mem,interest)

        class End(dict):
            def __init__(self):
                self['content'] = None
                pass








    Bot : discord.Client
    Guild : discord.Guild

    STATUS : bool = False

    parameterList : typing.Dict[str,typing.Any] = {}
    memberList : typing.Dict[str,memberData] = {}
    roleList : typing.Dict[str,roleData] = {}
    channelList : typing.Dict[str,channelData] = {}
    interestList : typing.Dict[str,interestData] = {}

    DATA : typing.Dict[str,GuildData] = {}


    roleTagList : roleType = {}

    def __init__(self,bot:discord.Client)-> None :
        MemberManagerBot.Bot = bot
        # for guild in bot.guilds:
        #     MemberManagerBot.DATA[str(guild.id)] = GuildData()
        MemberManagerBot.Guild = bot.guilds[0]#.get_guild(1423182810382073858)
        self.bot = bot

    @tasks.loop(seconds=3600)
    async def day_loop(self):
        try:
            print('1hour loop')
            
            try:
                self.Bot.git.push()
            except:
                print('git push error')
                pass

            try:
                await self.update_year_counter()
                await self.update_member_counter()
            except:
                pass

        except:
            pass

    async def loadEvent(self):
        load_result = {}
        is_error = False
        try:
            load_result = self.load_data()
            
            message_data = await self.generete_load_log_embed(load_result)
            await self.output_log(message_data)
            if not all(load_result.values()):
                raise
            await asyncio.sleep(1)

            print('セットアップ開始')

            await self.apply_all_member()
            await asyncio.sleep(1)

            print('ロール設定完了')

            self.day_loop.start()

            print('セットアップ完了')
            await self.debug_resend()
        except Exception as e:
            is_error = True
        finally:
            if all(load_result.values()) and not is_error:
                self.STATUS = True
                activity = discord.CustomActivity(name='正常に稼働しています')
                await self.Bot.change_presence(activity=activity,status=discord.Status.online)
            else:
                self.STATUS = False
                activity = discord.CustomActivity(name='セットアップに失敗しました')
                await self.Bot.change_presence(activity=activity,status=discord.Status.dnd)

        #await self.set_member_count()


    # イベント
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_interaction(self,itc: discord.Interaction):
        if (self.STATUS):
            if (itc.data.get('custom_id','').startswith('media_mgt')):
                if (itc.data.get('custom_id','').startswith('media_mgt_join')):
                    if (itc.message.id == MemberManagerBot.channelList.get('join',{}).get('message')):
                        await itc.response.send_message(**self.JoinWidget.Main(),ephemeral=True)
                elif (itc.data.get('custom_id','').startswith('media_mgt_update')):
                    if (itc.message.id == MemberManagerBot.channelList.get('update',{}).get('message')):
                        member = MemberManagerBot.memberList.get(str(itc.user.id))
                        if member['stop_count'] == 0:
                            await itc.response.defer(thinking=False,ephemeral=True)
                        if member['stop_count'] > 0:
                            await itc.response.send_message(**self.UpdateWidget.Main(member),ephemeral=True)
                elif (itc.data.get('custom_id','').startswith('media_mgt_interest')):
                    if (itc.message.id == MemberManagerBot.channelList.get('interest',{}).get('message')):
                        await itc.response.send_message(**self.InterestWidget.Main(MemberManagerBot.memberList.get(str(itc.user.id),{})),ephemeral=True)
                elif (itc.data.get('custom_id','').startswith('media_mgt_debug')):
                    await itc.response.defer(thinking=False,ephemeral=True)
                    try:
                        if (itc.data.get('custom_id','') == 'media_mgt_debug_command1'):
                            if (MemberManagerBot.memberList.get(str(itc.user.id)) is  None):
                                raise
                            MemberManagerBot.memberList[str(itc.user.id)]['stop_count'] += 1
                            await self.set_member_data(itc.user)
                            await itc.followup.send('更新回数を設定しました',ephemeral=True)
                            
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command2'):
                            if (MemberManagerBot.memberList.get(str(itc.user.id)) is  None):
                                raise
                            MemberManagerBot.memberList[str(itc.user.id)]['stop_count'] += 2
                            await self.set_member_data(itc.user)
                            await itc.followup.send('更新回数を設定しました',ephemeral=True)
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command3'):
                            if (MemberManagerBot.memberList.get(str(itc.user.id)) is  None):
                                raise
                            MemberManagerBot.memberList[str(itc.user.id)]['stop_count'] = 0
                            await self.set_member_data(itc.user)
                            await itc.followup.send('更新回数を設定しました',ephemeral=True)
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command4'):
                            if (MemberManagerBot.memberList.get(str(itc.user.id)) is  None):
                                raise
                            await self.clear_member_data(itc.user)
                            await itc.followup.send('メンバーのデータをクリアしました',ephemeral=True)
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command5'):
                            await itc.followup.send(str(self.memberList),ephemeral=True)
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command6'):
                            rank = 'visitor'

                            data = MemberManagerBot.memberList.get(str(itc.user.id),{})
                            data['rank'] = rank

                            await self.set_member_data(itc.user,data)

                            await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                            await self.output_log(self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command7'):
                            rank = 'member'

                            data = MemberManagerBot.memberList.get(str(itc.user.id),{})
                            data['rank'] = rank

                            await self.set_member_data(itc.user,data)

                            await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                            await self.output_log(self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command8'):
                            rank = 'staff'

                            data = MemberManagerBot.memberList.get(str(itc.user.id),{})
                            data['rank'] = rank

                            await self.set_member_data(itc.user,data)

                            await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                            await self.output_log(self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command9'):
                            rank = 'admin'

                            data = MemberManagerBot.memberList.get(str(itc.user.id),{})
                            data['rank'] = rank

                            await self.set_member_data(itc.user,data)

                            await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                            await self.output_log(self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                            pass
                        elif (itc.data.get('custom_id','') == 'media_mgt_debug_command10'):
                            rank = 'owner'

                            data = MemberManagerBot.memberList.get(str(itc.user.id),{})
                            data['rank'] = rank

                            await self.set_member_data(itc.user,data)

                            await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                            await self.output_log(self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                            pass
                        
                        else:
                            await itc.followup.send('不明なコマンド',ephemeral=True)
                    except Exception as e:
                        await itc.followup.send('エラーが発生しました',ephemeral=True)
            pass
        else:
            if (itc.data.get('custom_id','').startswith('media_mgt')):
                await itc.response.send_message('現在稼働していません',ephemeral=True)

    # コマンド
    # コマンド:チャンネル設定
    @discord.app_commands.command(name='media_mgt_set_channel',description='チャンネルを設定します')
    @discord.app_commands.choices(
        channel_type = [
            discord.app_commands.Choice(name='入会手続き用チャンネル',value='join'),
            discord.app_commands.Choice(name='更新手続き用チャンネル',value='update'),
            discord.app_commands.Choice(name='所属班設定用チャンネル',value='interest'),
            discord.app_commands.Choice(name='システムログチャンネル',value='log'),
            discord.app_commands.Choice(name='周年カウンター',value='year_counter'),
            discord.app_commands.Choice(name='会員カウンター',value='member_counter'),
        ]
    )
    @discord.app_commands.describe(channel_type='チャンネルの種類')
    @discord.app_commands.describe(channel='対象チャンネル. 省略時は現在のチャンネル')
    async def media_mgt_set_channel(
            self,
            ctx:discord.Interaction,
            channel_type:discord.app_commands.Choice[str],
            channel:discord.TextChannel=None
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        try:
            if channel_type.value not in ['join','update','interest','log','year_counter','member_counter']:
                raise InputError('channel_type')
            if channel is None:
                channel = ctx.channel

            message = None
            try:
                if channel_type.value == 'join':
                    message = await channel.send(self.JoinWidget.Start())
                elif channel_type.value == 'update':
                    message = await channel.send(self.UpdateWidget.Start())
                elif channel_type.value == 'interest':
                    message = await channel.send(self.InterestWidget.Start())
            except Exception as e:
                error_msg = 'チャンネルの送信に失敗しました'
                raise e

            MemberManagerBot.channelList[channel_type.value] = {
                'channel':channel.id,
                'message':message.id if (type(message) is discord.Message) else None
            }
            self.save_channel_data()

            await ctx.followup.send(f'{channel_type.name}を設定しました',ephemeral=True)
            await self.output_log(self.generate_command_log_embed(ctx,f'<#{channel.id}>を{channel_type.name}に設定しました'))

        except Exception as e:
            await ctx.followup.send('エラーが発生しました',ephemeral=True)
            await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))


    @discord.app_commands.command(name='media_mgt_set_category',description='カテゴリを設定します')
    @discord.app_commands.choices(
        category_type = [
            discord.app_commands.Choice(name='創作活動カテゴリ',value='creation'),
            discord.app_commands.Choice(name='非表示カテゴリ',value='hidden'),
        ]
    )
    @discord.app_commands.describe(category_type='カテゴリの種類')
    @discord.app_commands.describe(category='対象カテゴリ. 省略時は現在のチャンネルが属するカテゴリ')
    async def media_mgt_set_category(
            self,
            ctx:discord.Interaction,
            category_type:discord.app_commands.Choice[str],
            category:discord.CategoryChannel=None
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                if category_type.value not in ['creation','hidden']:
                    raise InputError('category_type')
                if category is None:
                    category = ctx.channel.category
                    if category is None:
                        raise InputError('category')
                MemberManagerBot.channelList[category_type.value] = {
                    'channel':category.id,
                    'message':None
                }
                self.save_channel_data()

                await ctx.followup.send(f'{category_type.name}を設定しました',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,f'<#{category.id}>を{category_type.name}に設定しました'))

            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
        else:
            await ctx.followup.send('メンバー管理ボットは現在正常に稼働していません',ephemeral=True)




    # コマンド:データ編集
    @discord.app_commands.command(name='media_mgt_view_mydata',description='自身の情報を表示します')
    async def media_mgt_view_mydata(self,ctx:discord.Interaction):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                data = self.memberList.get(str(ctx.user.id))
                if data is None:
                    error_msg = 'メンバー情報が見つかりません'
                    raise InputError('member')

                data = self.check_member_data(data)
                
                text = '```ansi\n'
                text += f'[1;2m[0m[2;37m[1;37m名　前：{data["name"]}\n'
                text += f'階　級：{RANK_DICT.get(data["rank"],'----')}\n'
                text += f'学　年：{GRADE_DICT.get(data["grade"],'----')}\n'
                text += f'コース：{COURSE_DICT.get(data["course"],'----')}\n'
                text += f'所属班：' + ','.join([f'{MemberManagerBot.interestList.get(i,{}).get("label")}' for i in data["interest"]])
                text += '[0m[2;37m[0m\n```'

                embed = discord.Embed(title=f'{ctx.user.name}さんの情報',description='データベースに登録されている情報を表示します',color=0x00ff00,timestamp=datetime.datetime.now())
                embed.set_author(name=ctx.user.name,icon_url=ctx.user.avatar.url)
                embed.add_field(name='メンバー情報',value=text)

                await ctx.followup.send(embed=embed,ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,'自分の情報を表示しました'))
            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
        else:
            await ctx.followup.send('メンバー管理ボットは現在正常に稼働していません',ephemeral=True)


    @discord.app_commands.command(name='media_mgt_view_member',description='メンバーの情報を表示します')
    @discord.app_commands.describe(member='対象のユーザー')
    async def media_mgt_view_member(self,ctx:discord.Interaction,member:discord.Member):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                data = self.memberList.get(str(member.id))
                if data is None:
                    error_msg = '指定したユーザーは登録されていません'
                    raise InputError('member')
                
                data = self.check_member_data(data)
                
                text = '```ansi\n'
                text += f'[1;2m[0m[2;37m[1;37m名　前：{data["name"]}\n'
                text += f'階　級：{RANK_DICT.get(data["rank"],'----')}\n'
                text += f'学　年：{GRADE_DICT.get(data["grade"],'----')}\n'
                text += f'コース：{COURSE_DICT.get(data["course"],'----')}\n'
                text += f'所属班：' + ','.join([f'{MemberManagerBot.interestList.get(i,{}).get("label")}' for i in data["interest"]])
                text += '[0m[2;37m[0m\n```'

                embed = discord.Embed(title=f'{member.name}さんの情報',description='データベースに登録されている情報を表示します',color=0x00ff00,timestamp=datetime.datetime.now())
                embed.set_author(name=member.name,icon_url=member.avatar.url)
                embed.add_field(name='メンバー情報',value=text)
                await ctx.followup.send(embed=embed,ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,f'<@{member.id}>さんの情報を表示しました'))
            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
        else:
            await ctx.followup.send('メンバー管理ボットは現在正常に稼働していません',ephemeral=True)


    @discord.app_commands.command(name='media_mgt_set_rank',description='メンバーのランクを設定します')
    @discord.app_commands.choices(
        rank=[
            discord.app_commands.Choice(name='見学',value='visitor'),
            discord.app_commands.Choice(name='会員',value='member'),
            discord.app_commands.Choice(name='役員',value='staff'),
            discord.app_commands.Choice(name='会長',value='admin'),
            discord.app_commands.Choice(name='卒業生',value='retirement'),
            discord.app_commands.Choice(name='顧問',value='consultant'),
        ]
    )
    @discord.app_commands.describe(member='対象メンバー')
    @discord.app_commands.describe(rank='メンバーのランク')
    async def media_mgt_set_rank(
            self,
            ctx:discord.Interaction,
            member:discord.Member,
            rank:discord.app_commands.Choice[str]
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                error_msg = 'ランクの照合に失敗しました'
                self.check_member_rank_editable(ctx.user,member,rank.value)


                data = MemberManagerBot.memberList.get(str(member.id),{})
                data['rank'] = rank.value

                await self.set_member_data(member,data)

                await ctx.followup.send('メンバーのランクを設定しました',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,'メンバーのランクを設定しました'))

            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
        else:
            await ctx.followup.send('メンバー管理ボットは現在正常に稼働していません',ephemeral=True)


    @discord.app_commands.command(name='media_mgt_edit_member',description='メンバー情報を編集します')
    @discord.app_commands.choices(
        rank=[
            discord.app_commands.Choice(name='見学',value='visitor'),
            discord.app_commands.Choice(name='会員',value='member'),
            discord.app_commands.Choice(name='役員',value='staff'),
            discord.app_commands.Choice(name='会長',value='admin'),
            discord.app_commands.Choice(name='卒業生',value='retirement'),
            discord.app_commands.Choice(name='顧問',value='consultant'),
        ]
    )
    @discord.app_commands.choices(
        grade = [
            discord.app_commands.Choice(name='1年',value='grade1'),
            discord.app_commands.Choice(name='2年',value='grade2'),
            discord.app_commands.Choice(name='3年',value='grade3'),
            discord.app_commands.Choice(name='4年',value='grade4'),
            discord.app_commands.Choice(name='5年',value='grade5'),
            discord.app_commands.Choice(name='専攻科',value='special'),
            discord.app_commands.Choice(name='OB・OG',value='graduation'),
            discord.app_commands.Choice(name='不明',value='unknown'),
        ]
    )
    @discord.app_commands.choices(
        course=[
            discord.app_commands.Choice(name='1-5',value='class5'),
            discord.app_commands.Choice(name='1-6',value='class6'),
            discord.app_commands.Choice(name='1-7',value='class7'),
            discord.app_commands.Choice(name='1-8',value='class8'),
            discord.app_commands.Choice(name='情報通信工学コース',value='courseT'),
            discord.app_commands.Choice(name='ロボット工学コース',value='courseR'),
            discord.app_commands.Choice(name='航空宇宙工学コース',value='courseA'),
            discord.app_commands.Choice(name='医療福祉工学コース',value='courseW'),
            discord.app_commands.Choice(name='不明',value='unknown'),
        ]
    )
    @discord.app_commands.describe(member='対象のユーザー')
    @discord.app_commands.describe(name='変更後の名前')
    @discord.app_commands.describe(rank='変更後のランク')
    @discord.app_commands.describe(grade='変更後の学年')
    @discord.app_commands.describe(course='変更後のコース')
    async def media_mgt_edit_member(
            self,
            ctx:discord.Interaction,
            member:discord.Member,
            name:str = None,
            rank:discord.app_commands.Choice[str] = None,
            grade:discord.app_commands.Choice[str] = None,
            course:discord.app_commands.Choice[str] = None
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                self.check_member_rank_editable(ctx.user,member,rank.value)

                data = {
                    'name':name,
                    'rank':rank.value if (rank is not None) else None,
                    'grade':grade.value if (grade is not None) else None,
                    'course':course.value if (course is not None) else None,
                    'interest':MemberManagerBot.memberList.get(str(member.id),{}).get('interest',[]),
                    'stop_count':0
                }

                flag = await self.set_member_data(member,data)
                if flag:
                    await ctx.followup.send('メンバー情報を編集しました',ephemeral=True)
                else:
                    await ctx.followup.send('メンバー情報を編集できません',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,'メンバー情報を編集しました'))

            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)



    @discord.app_commands.command(name='media_mgt_set_interest',description='メンバーの興味を設定します')
    @discord.app_commands.describe(member='対象のユーザー')
    @discord.app_commands.describe(mode='設定方法')
    @discord.app_commands.describe(interest='班')
    async def media_mgt_set_interest(self,ctx:discord.Interaction,member:discord.Member,mode:bool,interest:str):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                data = MemberManagerBot.memberList.get(str(member.id),{})
                if mode:
                    data['interest'].append(interest)
                else:
                    data['interest'].remove(interest)
                await self.set_member_data(member,data)
                await ctx.followup.send('メンバーの興味を設定しました',ephemeral=True)
                pass
            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))

        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)


    @discord.app_commands.command(name='media_mgt_clear_member',description='メンバーのデータをクリアします')
    @discord.app_commands.describe(member='対象メンバー')
    async def media_mgt_clear_member(self,ctx:discord.Interaction,member:discord.Member):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                flag = await self.clear_member_data(member)
                if (flag):
                    await ctx.followup.send('メンバーのデータをクリアしました',ephemeral=True)
                else:
                    await ctx.followup.send('メンバーのデータをクリアできません',ephemeral=True)
            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))

        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)



    # コマンド:班設定
    async def media_mgt_interest_auto(self,interaction:discord.Interaction,current:str) -> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=value['emoji']+value['label'],value=key) for key,value in MemberManagerBot.interestList.items() if
            (value['label'].startswith(current) or value['emoji'].startswith(current) or key.startswith(current))
            ]

    @discord.app_commands.command(name='media_mgt_add_interest',description='班を追加します')
    @discord.app_commands.describe(label='名前')
    @discord.app_commands.describe(value='内部識別子')
    @discord.app_commands.describe(emoji='絵文字')
    @discord.app_commands.describe(role='対応するロール')
    @discord.app_commands.describe(channel='対応するチャンネル')
    async def media_mgt_add_interest(
        self,
        ctx:discord.Interaction,
        label:str,
        value:str,
        emoji:str,
        role:discord.Role = None,
        channel:discord.TextChannel = None
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                # 値のチェック
                if (label in [interest['label'] for interest in MemberManagerBot.interestList.values()]):
                    raise InputError('label')
                if (value in MemberManagerBot.interestList.keys()):
                    raise InputError('value')
                if (emoji in [interest['emoji'] for interest in MemberManagerBot.interestList.values()] and (not is_emoji(emoji))):
                    raise InputError('emoji')
                
                index = min([MemberManagerBot.Guild.get_role(i['role_id']).position for i in MemberManagerBot.interestList.values()])
                if (role is None):
                    role = await ctx.guild.create_role(name=label)
                    await role.edit(position=index,color=MemberManagerBot.parameterList.get('interest_color',0))
                else:
                    await role.edit(name=label,position=index,color=MemberManagerBot.parameterList.get('interest_color',0))

                category = self.get_category_data('creation')
                if category is None:
                    raise
                index = max([i.position for i in category.text_channels])

                if (channel is None):
                    channel = await ctx.guild.create_text_channel(emoji+label,category=category,position=index)
                else:
                    await channel.edit(name=emoji+label,category=category,position=index)

                data : interestData = {
                    'label':label,
                    'emoji':emoji,
                    'role_id':role.id,
                    'channel_id':channel.id
                }
                MemberManagerBot.interestList[value] = data
                self.save_interest_data()

                await ctx.followup.send('班を追加しました',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,''))

                await self.resend_widget('interest')
                await self.apply_all_member()
            except Exception as e:
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                pass
        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)

        pass


    @discord.app_commands.command(name='media_mgt_edit_interest',description='班を編集します')
    @discord.app_commands.autocomplete(interest=media_mgt_interest_auto)
    @discord.app_commands.describe(interest='対象班')
    @discord.app_commands.describe(label='名前')
    @discord.app_commands.describe(value='内部識別子')
    @discord.app_commands.describe(emoji='絵文字')
    @discord.app_commands.describe(role='対応するロール')
    @discord.app_commands.describe(channel='対応するチャンネル')
    async def media_mgt_edit_interest(
        self,
        ctx:discord.Interaction,
        interest:str,
        label:str = None,
        value:str = None,
        emoji:str = None,
        role:discord.Role = None,
        channel:discord.TextChannel = None
    ):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                current = MemberManagerBot.interestList.get(interest)
                if (current is None):
                    raise InputError('interest')
                # 値のチェック
                if (label in [inter['label'] for inter in MemberManagerBot.interestList.values()]) and (label != current['label']):
                    raise InputError('label')
                if (value in MemberManagerBot.interestList.keys()) and (interest != value):
                    raise InputError('value')
                if (emoji in [inter['emoji'] for inter in MemberManagerBot.interestList.values()] and (not is_emoji(emoji))) and (emoji != current['emoji']):
                    raise InputError('emoji')
                
                if label is None:
                    label = current['label']
                if value is None:
                    value = interest
                if emoji is None:
                    emoji = current['emoji']
                
                error_msg = 'None'
                index = min([MemberManagerBot.Guild.get_role(i['role_id']).position for i in MemberManagerBot.interestList.values()])
                if (role is None):
                    role = await MemberManagerBot.Guild.get_role(current['role_id']).edit(name=label,color=MemberManagerBot.parameterList.get('interest_color',0),position=index)
                else:
                    await role.edit(name=label,color=MemberManagerBot.parameterList.get('interest_color',0),position=index)

                creation = self.get_category_data('creation')
                if (channel is None):
                    channel = MemberManagerBot.Guild.get_channel(current['channel_id'])
                    await channel.edit(name=emoji+label,category=creation)
                else:
                    ch = MemberManagerBot.Bot.get_channel(current['channel_id'])
                    hidden = self.get_category_data('hidden')
                    
                    await ch.edit(category=hidden)
                    await channel.edit(name=emoji+label,category=creation)
                
                del MemberManagerBot.interestList[interest]
                
                data : interestData = {
                    'label':current['label'] if label is None else label,
                    'emoji':current['emoji'] if label is None else emoji,
                    'channel_id':current['channel_id'] if label is None else channel.id,
                    'role_id':current['role_id'] if role is None else role.id
                }
                MemberManagerBot.interestList[value] = data
                self.save_interest_data()

                await ctx.followup.send('班を編集しました',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,''))

                await self.resend_widget('interest')
                for key,val in MemberManagerBot.memberList.items():
                    try:
                        interests = [value if i == interest else i for i in val.get('interest',[])]
                        if (interests != val.get('interest',[])):
                            MemberManagerBot.memberList[key]['interest'] = interests
                    except:
                        pass
                await self.apply_all_member()
            except Exception as e:
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                pass
        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)



    @discord.app_commands.command(name='media_mgt_remove_interest',description='班を削除します')
    @discord.app_commands.autocomplete(interest=media_mgt_interest_auto)
    @discord.app_commands.describe(interest='対象班')
    async def media_mgt_remove_interest(self,ctx:discord.Interaction,interest:str):
        await ctx.response.defer(thinking=False,ephemeral=True)
        error_msg = 'None'
        if self.STATUS:
            try:
                data = MemberManagerBot.interestList.get(interest)
                if (data is None):
                    await ctx.followup.send(f'{interest}が見つかりません',ephemeral=True)
                    raise

                channel = MemberManagerBot.Guild.get_channel(data['channel_id'])
                await channel.edit(category=MemberManagerBot.get_category_data('hidden'))

                role = MemberManagerBot.Guild.get_role(data['role_id'])
                await role.edit(position=1)

                del MemberManagerBot.interestList[interest]
                self.save_interest_data()

                await ctx.followup.send('班を削除しました',ephemeral=True)
                await self.output_log(self.generate_command_log_embed(ctx,''))

                await self.resend_widget('interest')
                await self.apply_all_member()
            except Exception as e:
                await ctx.followup.send('エラーが発生しました',ephemeral=True)
                await self.output_log(self.generate_command_error_log_embed(ctx,e,error_msg))
                pass
        else:
            await ctx.followup.send('メンバー管理ボットは動作していません',ephemeral=True)


        pass






    @discord.app_commands.command(name='test_command',description='テストコマンド.使用禁止')
    async def test_command(self,ctx:discord.Interaction):
        embed = discord.Embed(title='デバッグボタン')
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='CMD1',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_command1'))
        view.add_item(discord.ui.Button(label='CMD2',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command2'))
        view.add_item(discord.ui.Button(label='CMD3',style=discord.ButtonStyle.red,custom_id='media_mgt_debug_command3'))
        view.add_item(discord.ui.Button(label='CMD4',style=discord.ButtonStyle.grey,custom_id='media_mgt_debug_command4'))
        view.add_item(discord.ui.Button(label='CMD5',style=discord.ButtonStyle.grey,custom_id='media_mgt_debug_command5'))
        message = await ctx.channel.send(embed=embed,view=view)
        MemberManagerBot.channelList['debug'] = {
            'channel' : message.channel.id,
            'message' : message.id
        }
        self.save_channel_data()
        await ctx.response.send_message('テストコマンドを実行しました',ephemeral=True)
    

    @discord.app_commands.command(name='test_command2',description='テストコマンド2.使用禁止')
    async def test_command2(self,ctx:discord.Interaction):
        await ctx.response.defer(thinking=False,ephemeral=True)
        try:
            self.Bot.git.push()
        except:
            pass
        await ctx.followup.send('テストコマンド2を実行しました',ephemeral=True)



    # 関数

    # 関数:ロード/セーブ
    @staticmethod
    def load_data():
        result = {
            'parameterList':False,
            'channelList':False,
            'memberList':False,
            'interestList':False,
            'roleList':False
        }

        try:
            with open(os.path.join(SOURCE,'parameterList.json'),encoding='utf-8') as f:
                MemberManagerBot.parameterList = json.load(f)
            result['parameterList'] = True
        except:
            pass

        try:
            with open(os.path.join(SOURCE,'channelList.json'),encoding='utf-8') as f:
                MemberManagerBot.channelList = json.load(f)
            result['channelList'] = True
        except:
            pass

        try:
            with open(os.path.join(SOURCE,'memberList.json'),encoding='utf-8') as f:
                MemberManagerBot.memberList = json.load(f)
            result['memberList'] = True
        except:
            pass

        try:
            with open(os.path.join(SOURCE,'interestList.json'),encoding='utf-8') as f:
                MemberManagerBot.interestList = json.load(f)
            result['interestList'] = True
        except:
            pass

        try:
            with open(os.path.join(SOURCE,'roleList.json'),encoding='utf-8') as f:
                MemberManagerBot.roleList = json.load(f)

                for key,value in MemberManagerBot.roleList.items():
                    try:
                        MemberManagerBot.roleTagList.setdefault(value['type'],{})
                        MemberManagerBot.roleTagList[value['type']][value['name']] = roleTagData(
                            name=value['name'],
                            role_id=int(key),
                            display_name=value['display_name'],
                            value=value['value']
                        )
                    except:
                        pass

            result['roleList'] = True
        except:
            pass

        return result

    @classmethod
    async def load_channels(cls):
        result = {
            'join':False,
            'update':False,
            'interest':False,
            'log':False,
            'year_counter':False,
            'member_counter':False
        }

        for i in list(['join','update','interest']):
            try:
                m = await cls.get_message_data(i)
                result[i] = m is not None
            except:
                pass
        
        for i in list(['log','year_counter','member_counter']):
            try:
                result[i] = cls.get_channel_data(i) is not None
            except:
                pass
        
        for i in list(['creation','hidden']):
            try:
                result[i] = cls.get_category_data(i) is not None
            except:
                pass

        return result

    @classmethod
    def save_member_data(cls):
        with open(os.path.join(SOURCE,'memberList.json'),'w',encoding='utf-8') as f:
            json.dump(cls.memberList,f,indent=4,ensure_ascii=False)

    @classmethod
    def save_channel_data(cls):
        with open(os.path.join(SOURCE,'channelList.json'),'w',encoding='utf-8') as f:
            json.dump(cls.channelList,f,indent=4,ensure_ascii=False)

    @classmethod
    def save_interest_data(cls):
        with open(os.path.join(SOURCE,'interestList.json'),'w',encoding='utf-8') as f:
            json.dump(cls.interestList,f,indent=4,ensure_ascii=False)


    @staticmethod
    async def export_data():
        ch = MemberManagerBot.Bot.get_channel(MemberManagerBot.channelList.get('log').get('channel'))

        if ch is None:
            return

        await ch.send(file=discord.File(os.path.join(SOURCE,'channelList.json'),filename='channelList.json'))
        await ch.send(file=discord.File(os.path.join(SOURCE,'memberList.json'),filename='memberList.json'))
        await ch.send(file=discord.File(os.path.join(SOURCE,'roleList.json'),filename='roleList.json'))


    # 関数:ロールデータ
    @classmethod
    async def check_guild_role(cls):

        pass


    # 関数:チャンネルデータ
    @classmethod
    async def get_message_data(cls,widget:typing.Literal['join','update','interest']):
        try:
            channel = cls.Guild.get_channel(cls.channelList.get(widget,{}).get('channel'))
            message = await channel.fetch_message(cls.channelList.get(widget,{}).get('message'))
            return message
        except:
            return None

    @classmethod
    def get_channel_data(cls,ch:typing.Literal['log','member_counter','year_counter']):
        try:
            channel = cls.Guild.get_channel(cls.channelList.get(ch,{}).get('channel'))
            return channel
        except:
            return None

    @classmethod
    def get_category_data(cls,ch:typing.Literal['creation','hidden']):
        try:
            category = cls.Guild.get_channel(cls.channelList.get(ch,{}).get('channel'))
            return category
        except:
            return None


    @classmethod
    async def resend_widget(cls,widget:typing.Literal['join','update','interest']) -> bool:
        try:
            message = await cls.get_message_data(widget)
            if widget == 'join':
                await message.edit(**cls.JoinWidget.Start())
            elif widget == 'update':
                await message.edit(**cls.UpdateWidget.Start())
            elif widget == 'interest':
                await message.edit(**cls.InterestWidget.Start())

            return True
        except:
            return False



    # 関数:メンバーデータ編集
    @classmethod
    def check_member_rank_editable(cls,from_member:discord.Member,to_member:discord.Member,val:RANK):
        class RankValueError(Exception):
            def __init__(self,message:str):
                self.message = message

            def __str__(self):
                return self.message


        from_rank = cls.memberList.get(str(from_member.id),{}).get('rank')
        to_rank = cls.memberList.get(str(to_member.id),{}).get('rank')
        ranks = ['visitor','member','staff','admin','retirement','consultant','owner']

        if from_rank not in ranks:
            raise RankValueError('実行者のランクが取得できません')
        elif to_rank not in ranks:
            raise RankValueError('対象者のランクが取得できません')
        elif val not in ranks:
            raise RankValueError('値が不正です')


        from_val = cls.roleTagList['rank'].get(from_rank,{}).get('value',0)
        to_val = cls.roleTagList['rank'].get(to_rank,{}).get('value',0)
        val_val = cls.roleTagList['rank'].get(val,{}).get('value',0)

        if from_val <= to_val:
            raise RankValueError('対象は実行者より低いランクのユーザーである必要があります')
        if from_val <= val_val:
            raise RankValueError('実行者より低いランクしか付与できません')

    @classmethod
    def check_member_data(cls,data:memberData) -> typing.Union[memberData,None]:
        rank_values = [
            'visitor',
            'member',
            'staff',
            'admin',
            'retirement',
            'consultant',
            'owner'
        ]

        grade_values = [
            'graduation',
            'special',
            'grade1',
            'grade2',
            'grade3',
            'grade4',
            'grade5'
        ]

        course_values = [
            'class5',
            'class6',
            'class7',
            'class8',
            'courseT',
            'courseA',
            'courseR',
            'courseW'
        ]

        # データ型の確認、成型
        mold = {
            'name'  : str(data.get('name')),
            'rank'  : data.get('rank') if(data.get('rank') in rank_values) else '',
            'grade' : data.get('grade') if(data.get('grade') in grade_values) else '',
            'course': data.get('course') if(data.get('course') in course_values) else '',
            'interest':list(set([str(i) for i in data.get('interest',[]) if i in MemberManagerBot.interestList.keys()])),
            'stop_count': data.get('stop_count',0) if (type(data.get('stop_count',0)) is int) else 0
        }

        # データ値の確認
        try:
            if (mold['rank'] == ''): raise # ランク無しは通らない
            elif (mold['rank'] == 'owner'): pass
            elif (mold['rank'] == 'consultant'): pass # 顧問は無条件に通過
            elif (mold['rank'] == 'retirement'):
                if (mold['course'] == '' or mold['course'].startswith('class')): raise # 卒業生でコースが不正だと通らない
            elif (mold['grade'] == '' or mold['course'] == ''): raise # 学年、コース無しは通らない
            elif (mold['grade'] == 'grade1' and mold['course'].startswith('course')): raise
            elif (mold['grade'] != 'grade1' and mold['course'].startswith('class')): raise
        except:
            return None

        # データの成型
        if (mold['rank'] == 'consultant' or mold['rank'] == 'owner'):
            mold['stop_count'] = 0
            mold['grade'] = ''
            mold['course'] = ''
        elif (mold['rank'] == 'retirement'):
            mold['stop_count'] = 0
            mold['grade'] = 'graduation'
        elif (mold['grade'] == 'graduation'):
            mold['stop_count'] = 0
            if (mold['rank'] in ['staff','member']):
                mold['rank'] = 'retirement'

        return mold

    @classmethod
    async def set_member_role(cls,member:discord.Member,data:memberData = None) -> bool:
        if (type(member) is not discord.Member):
            return False

        # ロールの更新
        add_roles = []
        remove_roles = [role for role in member.roles if (str(role.id) in list(cls.roleList.keys())+[str(interest['role_id']) for interest in MemberManagerBot.interestList.values()])]

        add_roles_id = []
        if (data is None):
            pass
        elif (data['stop_count'] > 0):
            add_roles_id.append(cls.roleTagList.get('special_rank',{}).get('stop',{}).get('role_id',0))
        else:
            add_roles_id.append(cls.roleTagList.get('rank',{}).get(data['rank'],{}).get('role_id',0))
            add_roles_id.append(cls.roleTagList.get('grade',{}).get(data['grade'],{}).get('role_id',0))
            add_roles_id.append(cls.roleTagList.get('course',{}).get(data['course'],{}).get('role_id',0))
            for role in data['interest']:
                add_roles_id.append(cls.interestList.get(role,{}).get('role_id',0))

        add_roles = [member.guild.get_role(role_id) for role_id in add_roles_id]

        remove_roles = [role for role in remove_roles if (role not in add_roles)]

        if (len([role for role in remove_roles if (role is not None)]) > 0):
            print('remove',remove_roles)
            await member.remove_roles(*[role for role in remove_roles if (role not in add_roles)])
        if (len([role for role in add_roles if (role is not None) and (role not in member.roles)]) > 0):
            print('add',add_roles)
            await member.add_roles(*[role for role in add_roles if (role is not None)])

        return True

    @classmethod
    async def set_member_name(cls,member:discord.Member,data:memberData = None):
        name = ''

        if (data is None):
            name = None
        else:
            if (data['stop_count'] > 0):
                name = data['name']
            elif (data['rank'] == 'consultant'):
                name = f'顧問_{data["name"]}'
            else:
                if (data['grade'] == 'grade1'):
                    if   (data['course'] == 'class5'):name = '5組'
                    elif (data['course'] == 'class6'):name = '6組'
                    elif (data['course'] == 'class7'):name = '7組'
                    elif (data['course'] == 'class8'):name = '8組'
                elif (data['grade'] == 'special'):name = '専'
                elif (data['grade'] == 'graduation'):name = '卒'
                else:
                    if   (data['course'] == 'courseT'):name = 'T'
                    elif (data['course'] == 'courseR'):name = 'R'
                    elif (data['course'] == 'courseW'):name = 'W'
                    elif (data['course'] == 'courseA'):name = 'A'

                    if   (data['grade'] == 'grade2'):name += '2'
                    elif (data['grade'] == 'grade3'):name += '3'
                    elif (data['grade'] == 'grade4'):name += '4'
                    elif (data['grade'] == 'grade5'):name += '5'
                name += '_'

                name += data['name']

                for interest in data['interest']:
                    name += str(MemberManagerBot.interestList.get(interest,{}).get('emoji',''))

        if cls.Guild.owner_id != member.id : 
            if member.nick != name:
                print(member.nick,name)
                await member.edit(nick=name)
        pass


    @classmethod
    async def set_member_data(cls,member:discord.Member,data:memberData = None ,*, is_save:bool=True) -> bool:
        member_id = member.id
        if (data is None):
            data = MemberManagerBot.memberList.get(str(member_id),{})
        if (type(member) is not discord.Member):
            return False

        mold = MemberManagerBot.check_member_data(data)
        if (mold is None):
            return False


        # リストの更新
        MemberManagerBot.memberList[str(member_id)] = mold
        if is_save: MemberManagerBot.save_member_data()

        try:
            embed = MemberManagerBot.generate_edit_member_log_embed('',member,MemberManagerBot.memberList.get(str(member_id),{}),mold)
            await MemberManagerBot.output_log({'embed':embed})
        except:
            pass

        # ロールの更新
        await MemberManagerBot.set_member_role(member,mold)


        # ニックネームの更新
        await MemberManagerBot.set_member_name(member,mold)

        return True

    @classmethod
    async def clear_member_data(cls,member:discord.Member):
        if (type(member) is not discord.Member):
            return False
        if (str(member.id) not in cls.memberList.keys()):
            return False

        del cls.memberList[str(member.id)]
        cls.save_member_data()

        await cls.set_member_role(member)
        await cls.set_member_name(member)
        return True


    @classmethod
    async def apply_all_member(cls):
        print('apply_all_member')

        new_member_list : typing.Dict[str,memberData] = {}

        for member in cls.Guild.members:
            try:
                if cls.Guild.owner == member:
                    data = cls.check_member_data({'rank':'owner','name':'サーバー管理'})
                    await cls.set_member_role(member,data)
                    new_member_list[str(member.id)] = data

                elif str(member.id) in cls.memberList.keys():
                    data = cls.check_member_data(cls.memberList[str(member.id)])
                    await cls.set_member_role(member,data)
                    await cls.set_member_name(member,data)
                    if data is None : continue
                    new_member_list[str(member.id)] = data
                else:
                    await cls.set_member_role(member)
                    await cls.set_member_name(member)

            except Exception as e:
                pass
            finally:
                await asyncio.sleep(0.2)


        cls.memberList = new_member_list
        cls.save_member_data()

    @classmethod
    async def renewal_all_member(cls,year:int=1):
        for member_id in cls.memberList.keys():
            try:
                cls.memberList[member_id]['stop_count'] += year
            except:
                pass
        await cls.apply_all_member()


    # 関数:統計更新
    @classmethod
    async def update_year_counter(cls):
        ch = cls.Guild.get_channel(cls.channelList.get('year_counter',{}).get('channel',0))
        if ch is None:
            return
        
        try:
            name = ch.name
            val = int(re.search(r'\d+',name).group())

            now = int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'))

            if (now >= (val+1)*10000+start_time):
                v = val
                while (now >= (v+1)*10000+start_time):
                    v += 1
                
                print('更新する',val,v)
                await ch.edit(name=name.replace(str(val),str(v)))
                await cls.renewal_all_member(v-val)
            else:
                v = (now -start_time)//10000
                if v != val:
                    print('修正する',val,v)
                    await ch.edit(name=name.replace(str(val),str(v)))
                else:
                    print('更新不要',val,v)
        except:
            pass
        pass

    @classmethod
    async def update_member_counter(cls):
        ch = cls.Guild.get_channel(cls.channelList.get('member_counter',{}).get('channel',0))
        if ch is None:
            return

        try:
            name = ch.name
            val = int(re.search(r'\d+',name).group())

            v = val
            for member in cls.memberList.values():
                if member['rank'] in ['member','staff','admin']:
                    v += 1

            if v != val:
                await ch.edit(name=name.replace(str(val),str(v)))
        except:
            pass






    # 関数:ログ
    @staticmethod
    async def output_log(data):
        if MemberManagerBot.channelList.get('log',{}).get('channel') is None:
            return
        await MemberManagerBot.Bot.get_channel(MemberManagerBot.channelList['log']['channel']).send(**data)



    @staticmethod
    async def generete_load_log_embed(load_data:dict):
        file_log = ''
        for k,v in load_data.items():
            file_log += f'[2;33m{k: <12}[2;37m:[0m[2;33m[0m{'[2;32m[1;32m成功[0m[2;32m[0m' if v else '[2;31m[1;31m失敗[0m[2;31m[0m'}\n'
            pass

        channel_log = ''


        result = await MemberManagerBot.load_channels()
        for key,value in result.items():
            flag = value
            channel_log += f'[2;33m{key: <8}[2;37m:[0m[2;33m[0m{'[2;32m[1;32m接続成功[0m[2;32m[0m' if flag else '[2;31m[1;31m失敗[0m[2;31m[0m'}\n'


        embed = discord.Embed(title='ロード完了',description='ボットが起動しました',color=discord.Color.green())
        embed.add_field(name='ファイルロード',value=f'```ansi\n{file_log}```',inline=False)
        embed.add_field(name='チャンネルロード',value=f'```ansi\n{channel_log}```',inline=False)
        return {'embed':embed}

    @staticmethod
    def generate_edit_member_log_embed(reason:str,user:discord.User,before:memberData,after:memberData):
        embed = discord.Embed(
            title='メンバー情報が編集されました',
            description=f'<@{user.id}>',
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        embed.set_author(name = 'メンバー変更ログ')


        text_generator = lambda data: '```ansi\n'\
            f'名　前 : {data.get("name")}\n'\
            f'ランク : {data.get("rank")}\n'\
            f'学　年 : {data.get("grade")}\n'\
            f'コース : {data.get("course")}\n'\
            f'所　属 : {data.get("interest")}\n'\
            f'更新値 : {data.get("stop_count")}\n```'\

        embed.add_field(name = '変更前',value = text_generator(before),inline=True)
        embed.add_field(name = '変更後',value = text_generator(after) ,inline=True)

        return embed

    @staticmethod
    def generate_command_log_embed(ctx:discord.Interaction,description:str):
        embed = discord.Embed(
            title='コマンド実行ログ',
            description=f'コマンド：{ctx.command.name}\n使用者:<@{ctx.user.id}>\nチャンネル:<#{ctx.channel.id}>',
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        embed.add_field(name = '入力',value = '```ansi\n'+'\n'.join([f'{key}:{value}' for key,value in ctx.namespace.__dict__.items()])+'\n```',inline=False)
        embed.add_field(name = '実行結果',value = description,inline=False)
        return {'embed':embed}

    @classmethod
    def generate_command_error_log_embed(cls,ctx:discord.Interaction,error_data:Exception,description:str = 'None'):
        embed = discord.Embed(
            title='コマンドエラーログ',
            description = f'コマンド：{ctx.command.name}\n使用者：<@{ctx.user.id}>\nチャンネル：<#{ctx.channel.id}>',
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_author(name = str(error_data.__class__.__name__))
        embed.add_field(name = '入力',value = '```ansi\n'+'\n'.join([f'{key}:{value}' for key,value in ctx.namespace.__dict__.items()])+'\n```',inline=False)
        embed.add_field(name = 'エラー詳細',value = str(error_data.args),inline=False)
        embed.add_field(name = '備考',value = description,inline=False)
        return {'embed':embed}

    @staticmethod
    def generate_error_embed(error_data:Exception,description:str):
        embed = discord.Embed(title=error_data.__class__.__name__,description=description,color=discord.Color.red())
        embed.set_author(name = 'エラー発生')
        embed.set_footer(text = error_data.args)
        return embed

    @staticmethod
    def generate_command_error_embed(error_data:Exception,ctx:discord.Interaction,description:str):
        embed = discord.Embed(
            title='コマンドエラー',
            description=f'コマンド：{ctx.command.name}\n使用者：<@{ctx.user.id}>\nチャンネル：<#{ctx.channel.id}>',
            color=discord.Color.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        embed.set_author(name = 'エラー発生')
        embed.add_field(name = '詳細',value = description,inline=False)
        embed.add_field(name = 'エラータイプ',value = str(error_data.__class__.__name__),inline=False)
        embed.set_footer(str(error_data.args))
        return embed


    # デバッグ
    @classmethod
    async def debug_resend(cls):
        try:
            ch = cls.Guild.get_channel(cls.channelList.get('debug',{}).get('channel',0))
            message = await ch.fetch_message(cls.channelList.get('debug',{}).get('message',0))

            embed = discord.Embed(title='デバッグパネル',description='メンバー管理ボットのデバッグパネル',color=0xff8000)
            embed.add_field(
                name='ボタン説明',
                value='' \
                    '更新+1:更新回数を1増やす\n'\
                    '更新+2:更新回数を2増やす\n' \
                    '更新=0:更新回数を0にする\n' \
                    'クリア:メンバーデータをクリアする\n' \
                    '表示:メンバーデータ一覧を表示する\n' \
                '')
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label='更新+1',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command1',row=0))
            view.add_item(discord.ui.Button(label='更新+2',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command2',row=0))
            view.add_item(discord.ui.Button(label='更新=0',style=discord.ButtonStyle.grey,custom_id='media_mgt_debug_command3',row=0))
            view.add_item(discord.ui.Button(label='クリア',style=discord.ButtonStyle.red,custom_id='media_mgt_debug_command4',row=0))
            view.add_item(discord.ui.Button(label='表示',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_command5',row=0))
            view.add_item(discord.ui.Button(label='見学',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command6',row=1))
            view.add_item(discord.ui.Button(label='会員',style=discord.ButtonStyle.gray,custom_id='media_mgt_debug_command7',row=1))
            view.add_item(discord.ui.Button(label='幹部',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command8',row=1))
            view.add_item(discord.ui.Button(label='会長',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_command9',row=1))
            view.add_item(discord.ui.Button(label='管理',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_command10',row=1))
            await message.edit(embed=embed,view=view)

        except:
            pass


# Cogのセットアップ
async def setup(bot):
    global BOT
    BOT = bot
    await bot.add_cog(m:=MemberManagerBot(bot))
    await m.loadEvent()
