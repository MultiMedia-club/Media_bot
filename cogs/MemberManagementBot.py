import os
import copy
import typing
import asyncio
import enum
import json
import datetime
import re
import glob
import functools
from typing import Union

from emoji import is_emoji

import discord
from discord.ext import commands
from discord.ext import tasks

#import main
#from ..main import MediaBot

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

class FaildError(Exception):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

class InputError(FaildError):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}の値が不正です'
        pass

class NoMemberError(FaildError):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}のデータが見つかりません'
        pass

class NoChannelError(FaildError):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}が見つかりません'
        pass

class MemberDataError(FaildError):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}'
        pass

class FailedMemberEditError(FaildError):
    arg = ''

    def __init__(self,arg:str):
        self.arg = arg
        pass

    def __str__(self):
        return f'{self.arg}'
        pass


class memberData(typing.TypedDict):
    name       : str
    rank       : RANK
    grade      : GRADE
    course     : COURSE
    interest  : typing.List[str]
    stop_count : int
    lock       : int

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

#!B guildData
class GuildData:
    state      : bool = False

    guild_id   : int
    source     : str

    parameters : typing.Dict[str,typing.Any]   = {}
    members    : typing.Dict[str,memberData]   = {}
    roles      : typing.Dict[str,roleData]     = {}
    channels   : typing.Dict[str,channelData]  = {}
    interests  : typing.Dict[str,interestData] = {}

    role_tags  : typing.Dict[str,roleTagData] = {}


    def __init__(self,guild_id:int):
        self.guild_id = guild_id

        self.source = os.path.join(SOURCE,str(self.guild_id))

        os.makedirs(self.source, exist_ok=True)

        if not os.path.exists(os.path.join(self.source,'parameterList.json')):
            self.parameters = {}
        else:
            with open(os.path.join(self.source,'parameterList.json'),encoding='utf-8') as f:
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

                for key,value in self.roles.items():
                    try:
                        self.role_tags.setdefault(value['type'],{})
                        self.role_tags[value['type']][value['name']] = roleTagData(
                            name=value['name'],
                            role_id=int(key),
                            display_name=value['display_name'],
                            value=value['value']
                        )
                    except:
                        pass

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

        self.state = True
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
        with open(os.path.join(self.source,'parameterList.json'),'w',encoding='utf-8') as f:
            json.dump(self.parameters,f,indent=4,ensure_ascii=False)
        pass



    def get_guild(self) -> discord.Guild:
        return MemberManagerBot.Bot.get_guild(self.guild_id)


    # メンバーデータ
    def get_member_data(self,member: Union[discord.Member,discord.User,int,str]) -> Union[memberData,None]:
        # 型確認
        member_id = 0

        if (type(member) == discord.Member):
            member_id = str(member.id)
        elif (type(member) == discord.User):
            member_id = str(member.id)
        elif (type(member) == int):
            member_id = str(member)
        elif (type(member) == str):
            if member.isdecimal():
                member_id = member
            else:
                raise ValueError('無効なメンバーIDです')
        else:
            raise TypeError('メンバーIDを指定してください。')
        
        # データの取得
        if member_id in self.members.keys():
            return copy.deepcopy(self.members[member_id])
        else:
            return None


    def check_member_data(self,data:memberData) -> typing.Union[memberData,None]:
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
            'interest':sorted(list(set([str(i) for i in data.get('interest',[]) if i in self.interests.keys()]))),
            'stop_count': data.get('stop_count',0) if (type(data.get('stop_count',0)) is int) else 0,
            'lock': data.get('lock',0) if (type(data.get('lock',0)) is int) else 0
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


    async def set_member_role(self,member: discord.Member,data:memberData = None) -> bool:
        if (type(member) is not discord.Member):
            return False

        # ロールの更新
        add_roles = []
        remove_roles = [
            role for role in member.roles if (str(role.id) in self.get_role_id_list())]

        add_roles_id = []
        if (data is None):
            pass
        elif (data['lock'] > self.get_now()):
            add_roles_id.append(self.role_tags.get('special_rank',{}).get('lock',{}).get('role_id',0))
            pass
        elif (data['stop_count'] > 0):
            add_roles_id.append(self.role_tags.get('special_rank',{}).get('stop',{}).get('role_id',0))
        else:
            add_roles_id.append(self.role_tags.get('rank',{}).get(data['rank'],{}).get('role_id',0))
            add_roles_id.append(self.role_tags.get('grade',{}).get(data['grade'],{}).get('role_id',0))
            add_roles_id.append(self.role_tags.get('course',{}).get(data['course'],{}).get('role_id',0))
            for role in data['interest']:
                add_roles_id.append(self.interests.get(role,{}).get('role_id',0))

        add_roles = [member.guild.get_role(role_id) for role_id in add_roles_id]

        remove_roles = [role for role in remove_roles if (role not in add_roles   ) and (role is not None)]
        add_roles    = [role for role in add_roles    if (role not in member.roles) and (role is not None)]

        if (len(remove_roles) > 0):
            print(f'[{self.get_now_str()}]REMOVE MEMBER_ROLE:{member.name}({member.id}) {remove_roles}')
            await member.remove_roles(*remove_roles)
        if (len(add_roles) > 0):
            print(f'[{self.get_now_str()}]ADD MEMBER_ROLE:{member.name}({member.id}) {add_roles}')
            await member.add_roles(*add_roles)

        return True
    

    async def set_member_name(self,member: discord.Member,data:memberData = None) -> bool:
        name = ''

        if (data is None):
            name = None
        else:
            if (data['lock'] > (d:=self.get_now())):
                val = '999+' if data['lock'] - d > 999 else str(data['lock'] - d)
                name = data['name'] + f'_残り{val}日'
            if (data['stop_count'] > 0):
                name = data['name']
            elif (data['rank'] == 'consultant'):
                name = f'顧問_{data["name"]}'
            else:
                if (data['grade'] == 'special'       ):name = '専'
                elif (data['grade'] == 'graduation'  ):name = '卒'
                elif (data['grade'] == 'grade1'):
                    if   (data['course'] == 'class5' ):name = '5組'
                    elif (data['course'] == 'class6' ):name = '6組'
                    elif (data['course'] == 'class7' ):name = '7組'
                    elif (data['course'] == 'class8' ):name = '8組'
                else:
                    if   (data['course'] == 'courseT'):name = 'T'
                    elif (data['course'] == 'courseR'):name = 'R'
                    elif (data['course'] == 'courseW'):name = 'W'
                    elif (data['course'] == 'courseA'):name = 'A'

                    if   (data['grade'] == 'grade2'  ):name += '2'
                    elif (data['grade'] == 'grade3'  ):name += '3'
                    elif (data['grade'] == 'grade4'  ):name += '4'
                    elif (data['grade'] == 'grade5'  ):name += '5'
                name += '_'

                name += data['name'][:24]

                for interest in data['interest']:
                    name += str(self.interests.get(interest,{}).get('emoji',''))
                name = name.replace('︎','').replace('️','')

        if member.guild.owner_id != member.id :
            if member.nick != name:
                print(f'[{self.get_now_str()}]EDIT MEMBER_NAME:{member.name}({member.id}) {member.nick} -> {name}')
                await member.edit(nick=name)


    async def set_member_data(self,member: discord.Member,data:memberData = None) -> bool:
        member_id = 0

        # 型確認
        if (type(member) == discord.Member):
            member_id = str(member.id)
        else:
            raise TypeError('メンバーIDを指定してください。')
        
        member_data = None
        
        if (data is None):
            if (member_id in self.members):
                del self.members[member_id]
        else:
            member_data = self.check_member_data(data)

            if member_data == None:
                return False
        
            self.members[member_id] = member_data
        
        self.save_member_data()

        self.set_member_role(member,member_data)
        self.set_member_name(member,member_data)

        return True


    def vs_member_rank(self,member1: discord.Member,member2: discord.Member) -> bool:
        rank1 = self.role_tags.get('rank',{}).get(self.get_member_data(member1)['rank'],{}).get('rank',0)
        rank2 = self.role_tags.get('rank',{}).get(self.get_member_data(member2)['rank'],{}).get('rank',0)

        return rank1 > rank2


    async def clear_member_data(self,member: discord.Member) -> bool:
        member_id = 0

        # 型確認
        if (type(member) == discord.Member):
            member_id = str(member.id)
        else:
            raise TypeError('メンバーIDを指定してください。')

        return await self.set_member_data(member,None)
    

    async def apply_all_member_data(self):
        new_members = {}
        guild = self.get_guild()

        for member in guild.members:
            try:
                if member.id == guild.owner_id:
                    member_data = self.check_member_data(member,{'rank':'owner','name':'サーバー管理'})
                    self.set_member_role(member,member_data)
                elif str(member.id) in self.members:
                    member_data = self.check_member_data(member,self.get_member_data(member))
                    self.set_member_role(member,member_data)
                    self.set_member_name(member,member_data)
                else:
                    self.set_member_role(member,None)
                    self.set_member_name(member,None)

                new_members[str(member.id)] = member_data
            except Exception as e:
                print(e)
                pass

        self.members = new_members

        self.save_member_data()
    
    async def renewal_all_member(self,year:int=1):
        for member_id in self.members.keys():
            try:
                member_data = self.get_member_data(member_id)
                member_data['stop_count'] += year
                await self.set_member_data(member_id,member_data)
            except:
                pass


    



    def get_now(self) -> int:
        return int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'))
    
    def get_now_str(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).strftime('%Y/%m/%d %H:%M:%S')


    def get_role_id_list(self) -> list:
        return list(self.roles.keys())+[str(interest['role_id']) for interest in self.interests.values()]

    




class TestWidget(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='名前を入力してください。')
        self.item = discord.ui.TextInput(label='名前',placeholder='名前',min_length=1,max_length=24,style=discord.TextStyle.short)
        self.add_item(self.item)
    
    async def on_submit(self,interaction:discord.Interaction):
        try:
            await interaction.response.defer(thinking=False,ephemeral=True)

            data = MemberManagerBot.DATA[str(interaction.guild.id)].members[str(interaction.user.id)]
            data['name'] = self.item.value

            await MemberManagerBot.set_member_data(interaction.user,data)

            await interaction.followup.send('名前を変更しました',ephemeral=True)
        except Exception as e:
            print(e)




class MemberManagerBot(commands.Cog):
    # ウィジェット !B
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
                self['view']  = self.View()

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
                            style = discord.TextStyle.short,
                            min_length=1,
                            max_length=24
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

                        try:
                            embed = discord.Embed(
                                title = '入会手続き',
                                description = f'実行者:<@{interaction.user.id}>\n名前：{self.item.value}\n学年：{GRADE_DICT.get(self.grade,"--")}\nコース：{COURSE_DICT.get(self.course,"--")}\n入会手続きに成功しました',
                                color = 0x8866cc,
                                timestamp = datetime.datetime.now()
                            )
                            embed.set_author(name = '入会手続きウィジェット')
                            await MemberManagerBot.output_log(interaction.guild,{'embed':embed})
                        except:
                            pass

                        
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

                    try:
                        embed = discord.Embed(
                            title='更新手続きが完了しました',
                            description=f'実行者:<@{interaction.user.id}>\n変更前：{self.member["grade"]}:{self.member["course"]}\n変更後：{self.grade}:{self.course}',
                            color=0xffff00,
                            timestamp=datetime.datetime.now(datetime.timezone.utc)
                        )
                        embed.set_author(name = '更新ウィジェット')
                        await MemberManagerBot.output_log(interaction.guild,{'embed':embed})
                    except:
                        pass

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
                def __init__(self,guild:discord.Guild):
                    super().__init__(
                        title = '所属班設定',
                        description = '所属する班を設定します',
                        color = 0x8866cc
                    )

                    self.add_field(name='班一覧',value='\n'.join([f'{v["emoji"].replace("︎","").replace("️","")}：{v["label"]}' for k,v in MemberManagerBot.DATA[str(guild.id)].interests.items()]))
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

            def __init__(self,guild:discord.Guild):
                self['embed'] = self.Embed(guild)
                self['view'] = self.View()

        class Main(dict):
            class Embed(discord.Embed):
                def __init__(self,guild:discord.Guild,mem:memberData):
                    interests = MemberManagerBot.DATA[str(guild.id)].interests
                    super().__init__(
                        title = '現在の所属班',
                        description = '\n'.join([f'{interests[i]["emoji"].replace("︎","").replace("️","")}:{interests[i]["label"]}' for i in mem.get('interest',[]) if i in interests.keys()]),
                        color = 0x8866cc
                    )


            class View(discord.ui.View):
                flag = False
                def __init__(self,guild:discord.Guild,mem:memberData,interest:typing.List[str]):
                    super().__init__()
                    self.guild = guild
                    self.interests = MemberManagerBot.DATA[str(guild.id)].interests
                    self.mem = mem
                    self.interest = interest
                    for key,value in self.interests.items():
                        btn = discord.ui.Button(
                            style = discord.ButtonStyle.green if (key in self.interest) else discord.ButtonStyle.grey,
                            custom_id = key,
                            emoji = value['emoji'].replace('︎','').replace('️','')
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

                    data = self.interests.get(interaction.data.get('custom_id',''))
                    if data is not None:
                        if interaction.data.get('custom_id','') in self.interest:
                            self.interest.remove(interaction.data.get('custom_id',''))
                        else:
                            self.interest.append(interaction.data.get('custom_id',''))

                    await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.InterestWidget.Main(self.guild,self.mem,self.interest))

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
                    before = data.get('interest',[])
                    data['interest'] = self.interest

                    try:
                        embed = discord.Embed(
                            title='所属班が変更されました',
                            description=f'実行者:<@{interaction.user.id}>\n変更前：{",".join([self.interests[i]['label'] for i in before])}\n変更後：{",".join([self.interests[i]['label'] for i in self.interest])}',
                            color = 0xffff00,
                            timestamp=datetime.datetime.now(datetime.timezone.utc)
                        )
                        embed.set_author(name = '所属班設定ウィジェット')
                        await MemberManagerBot.output_log(interaction.guild,{'embed':embed})
                    except:
                        pass

                    await MemberManagerBot.set_member_data(interaction.user,data)
                    await interaction.followup.edit_message(interaction.message.id,**MemberManagerBot.InterestWidget.End())

                    await interaction.followup.delete_message(interaction.message.id)



            def __init__(self,guild:discord.Guild,mem:memberData,interest:typing.List[str]=None):
                if interest is  None:
                    interest = mem.get('interest',[]).copy()
                self['content'] = '💡:使い方がわからない、正常に動作しない時は質問して下さい'
                self['embed'] = self.Embed(guild,mem)
                self['view'] = self.View(guild,mem,interest)

        class End(dict):
            def __init__(self):
                self['content'] = None
                pass


    # クラス変数 !B
    INSTANCE = None

    Bot : discord.Client

    STATUS : bool = False

    DATA : typing.Dict[str,GuildData] = {}



    def __init__(self,bot:discord.Client)-> None :
        MemberManagerBot.Bot = bot
        MemberManagerBot.INSTANCE = self

    @tasks.loop(seconds=3600)
    async def mgt_hour_loop(self):
        try:
            for guild in self.Bot.guilds:
                data = self.DATA.get(str(guild.id),None)
                data.state = False
                try:
                    await self.update_year_counter(guild)
                except:
                    pass

                try:
                    await self.update_member_counter(guild)
                except:
                    pass

                try:
                    await self.apply_all_member(guild)
                except:
                    pass
                data.state = True
        except:
            pass

    @classmethod
    async def loadEvent(cls):
        folders = [os.path.basename(folder) for folder in glob.glob(os.path.join(SOURCE,'*'))]

        state = True

        for guild in cls.Bot.guilds:
            if str(guild.id) not in folders:
                continue
            try:
                print('load',guild.name)
                load_result = {
                    'channelList':True,
                    'memberList':True,
                    'roleList':True,
                    'interestList':True,
                    'parameterList':True
                }

                MemberManagerBot.DATA[str(guild.id)] = GuildData(guild.id)

                message_data = await cls.generete_load_log_embed(guild,load_result)
                await cls.output_log(guild,message_data)
                if not all(load_result.values()):
                    raise

                for i in ['join','update','interest']:
                    try:
                        await cls.resend_widget(guild,i)
                    except:
                        pass

                await cls.debug_resend(guild)

                state &= True
            except Exception as e:
                print(e)
                state &= False

        cls.INSTANCE.mgt_hour_loop.start()

        await cls.Bot.set_cog_state('MemberManagementBot',0 if state else 2)
        cls.STATUS = state



    # イベント !B
    @commands.Cog.listener()
    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_interaction(self,itc: discord.Interaction):
        if (itc.data.get('custom_id','').startswith('media_mgt')):
            guild_data = MemberManagerBot.DATA.get(str(itc.guild.id))
            if guild_data is None:
                await itc.followup.send('このサーバーのデータが見つかりません',ephemeral=True)
                return
            if not guild_data.state:
                await itc.followup.send('このボットは現在正常に動作していません',ephemeral=True)
                return


            if (itc.data.get('custom_id','').startswith('media_mgt')):
                if (itc.data.get('custom_id','').startswith('media_mgt_join')):
                    if (itc.message.id == guild_data.channels.get('join',{}).get('message')):
                        if (guild_data.members.get(str(itc.user.id)) is not None):
                            await itc.response.send_message('既に登録済みです',ephemeral=True)
                        else:
                            await itc.response.send_message(**self.JoinWidget.Main(),ephemeral=True)
                elif (itc.data.get('custom_id','').startswith('media_mgt_update')):
                    if (itc.message.id == guild_data.channels.get('update',{}).get('message')):
                        member = guild_data.members.get(str(itc.user.id))
                        if member is None:
                            await itc.response.send_message('メンバー情報が見つかりません',ephemeral=True)
                        elif member['stop_count'] <= 0:
                            await itc.response.send_message('更新手続きの条件を満たしていません',ephemeral=True)
                        elif member['stop_count'] > 0:
                            await itc.response.send_message(**self.UpdateWidget.Main(member),ephemeral=True)
                elif (itc.data.get('custom_id','').startswith('media_mgt_interest')):
                    if (itc.message.id == guild_data.channels.get('interest',{}).get('message')):
                        if (guild_data.members.get(str(itc.user.id)) is None):
                            await itc.response.send_message('メンバー情報が見つかりません',ephemeral=True)
                        else:
                            await itc.response.send_message(**self.InterestWidget.Main(itc.guild,guild_data.members.get(str(itc.user.id),[])),ephemeral=True)
                
                elif (itc.data.get('custom_id','').startswith('media_mgt_debug')):
                    if (itc.data.get('custom_id','') == 'media_mgt_debug_name'):
                        if (guild_data.members.get(str(itc.user.id),{}).get('grade') == 'graduation'):
                            await itc.response.send_message('このイベントは卒業したメンバーのみ利用できます',ephemeral=True)
                        else:
                            await itc.response.send_modal(TestWidget())
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_reset'):
                        if (guild_data.members.get(str(itc.user.id)) is None):
                            await itc.response.send_message('メンバー情報が見つかりません',ephemeral=True)
                        else:
                            await itc.response.defer(thinking=False,ephemeral=True)
                            try:
                                await self.clear_member_data(itc.user)
                                await itc.followup.send('データをリセットしました',ephemeral=True)
                            except:
                                await itc.followup.send('リセットに失敗しました',ephemeral=True)
                    
                    elif (itc.data.get('custom_id','').startswith('media_mgt_debug_course')):
                        if (guild_data.members.get(str(itc.user.id),{}).get('grade') == 'graduation'):
                            await itc.response.send_message('このイベントは卒業したメンバーのみ利用できます',ephemeral=True)
                        else:
                            await itc.response.defer(thinking=False,ephemeral=True)
                            try:
                                if (itc.data.get('custom_id','') == 'media_mgt_debug_courseT'):
                                    data = guild_data.members.get(str(itc.user.id),{})
                                    data['course'] = 'courseT'
                                    await self.set_member_data(itc.user,data)
                                    await itc.followup.send('コースを設定しました',ephemeral=True)
                                elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseR'):
                                    data = guild_data.members.get(str(itc.user.id),{})
                                    data['course'] = 'courseR'
                                    await self.set_member_data(itc.user,data)
                                    await itc.followup.send('コースを設定しました',ephemeral=True)
                                elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseA'):
                                    data = guild_data.members.get(str(itc.user.id),{})
                                    data['course'] = 'courseA'
                                    await self.set_member_data(itc.user,data)
                                    await itc.followup.send('コースを設定しました',ephemeral=True)
                                elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseW'):
                                    data = guild_data.members.get(str(itc.user.id),{})
                                    data['course'] = 'courseW'
                                    await self.set_member_data(itc.user,data)
                                    await itc.followup.send('コースを設定しました',ephemeral=True)
                            except:
                                await itc.followup.send('コース設定に失敗しました',ephemeral=True)

                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_reset'):
                        await self.clear_member_data(itc.user)
                        await itc.followup.send('データをリセットしました',ephemeral=True)
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseT'):
                        data = guild_data.members.get(str(itc.user.id),{})
                        data['course'] = 'courseT'
                        await self.set_member_data(itc.user,data)
                        await itc.followup.send('コースを設定しました',ephemeral=True)
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseR'):
                        data = guild_data.members.get(str(itc.user.id),{})
                        data['course'] = 'courseR'
                        await self.set_member_data(itc.user,data)
                        await itc.followup.send('コースを設定しました',ephemeral=True)
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseA'):
                        data = guild_data.members.get(str(itc.user.id),{})
                        data['course'] = 'courseA'
                        await self.set_member_data(itc.user,data)
                        await itc.followup.send('コースを設定しました',ephemeral=True)
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_courseW'):
                        data = guild_data.members.get(str(itc.user.id),{})
                        data['course'] = 'courseW'
                        await self.set_member_data(itc.user,data)
                        await itc.followup.send('コースを設定しました',ephemeral=True)
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_name'):
                        modal = discord.ui.Modal(title='名前変更',custom_id='media_mgt_debug_name_set')
                        name_input = discord.ui.TextInput(label='名前',placeholder='名前',style=discord.TextInputStyle.short)
                        modal.add_item(name_input)
                        await itc.response.send_modal(modal)
                        pass

                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command1'):
                        if (guild_data.members.get(str(itc.user.id)) is  None):
                            raise
                        guild_data.members[str(itc.user.id)]['stop_count'] += 1
                        await self.set_member_data(itc.user)
                        await itc.followup.send('更新回数を設定しました',ephemeral=True)

                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command2'):
                        if (guild_data.members.get(str(itc.user.id)) is  None):
                            raise
                        guild_data.members[str(itc.user.id)]['stop_count'] += 2
                        await self.set_member_data(itc.user)
                        await itc.followup.send('更新回数を設定しました',ephemeral=True)
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command3'):
                        if (guild_data.members.get(str(itc.user.id)) is  None):
                            raise
                        guild_data.members[str(itc.user.id)]['stop_count'] = 0
                        await self.set_member_data(itc.user)
                        await itc.followup.send('更新回数を設定しました',ephemeral=True)
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command4'):
                        if (guild_data.members.get(str(itc.user.id)) is  None):
                            raise
                        await self.clear_member_data(itc.user)
                        await itc.followup.send('メンバーのデータをクリアしました',ephemeral=True)
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command5'):
                        await itc.followup.send(str(guild_data.members),ephemeral=True)
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command6'):
                        rank = 'visitor'

                        data = guild_data.members.get(str(itc.user.id),{})
                        data['rank'] = rank

                        await self.set_member_data(itc.user,data)

                        await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                        await self.output_log(itc.guild,self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command7'):
                        rank = 'member'

                        data = guild_data.members.get(str(itc.user.id),{})
                        data['rank'] = rank

                        await self.set_member_data(itc.user,data)

                        await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                        await self.output_log(itc.guild,self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command8'):
                        rank = 'staff'

                        data = guild_data.members.get(str(itc.user.id),{})
                        data['rank'] = rank

                        await self.set_member_data(itc.user,data)

                        await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                        await self.output_log(itc.guild,self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command9'):
                        rank = 'admin'

                        data = guild_data.members.get(str(itc.user.id),{})
                        data['rank'] = rank

                        await self.set_member_data(itc.user,data)

                        await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                        await self.output_log(itc.guild,self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                        pass
                    elif (itc.data.get('custom_id','') == 'media_mgt_debug_command10'):
                        rank = 'owner'

                        data = guild_data.members.get(str(itc.user.id),{})
                        data['rank'] = rank

                        await self.set_member_data(itc.user,data)

                        await itc.followup.send('メンバーのランクを設定しました',ephemeral=True)
                        await self.output_log(itc.guild,self.generate_command_log_embed(itc,'メンバーのランクを設定しました'))
                        pass

                    else:
                        await itc.followup.send('不明なコマンド',ephemeral=True)



    # コマンド !B
    def command_checker(func):
        @functools.wraps(func)
        async def wrapper(self,ctx:discord.Interaction,**kwargs):
            await ctx.response.defer(thinking=False,ephemeral=True)

            guild_data = MemberManagerBot.DATA.get(str(ctx.guild.id))

            if guild_data is None:
                await ctx.followup.send('このサーバーのデータが見つかりません',ephemeral=True)
                return
            if not guild_data.state:
                await ctx.followup.send('このボットは現在正常に動作していません',ephemeral=True)
                return

            ctx.extras['data'] = guild_data
            ctx.extras['process'] = 'func'

            res = {'content':'None'}
            log = {'content':'None'}

            try:
                res,log = await func(self,ctx,**kwargs)
            except Exception as e:
                if isinstance(e,FaildError):
                    res = {'content':f'エラーが発生しました\n{e.arg}'}
                    log = MemberManagerBot.generate_command_failed_log_embed(ctx,e,ctx.extras['process'])
                else:
                    res = {'content':'エラーが発生しました'}
                    log = MemberManagerBot.generate_command_error_log_embed(ctx,e,'不明なエラー')
            finally:
                message = await ctx.followup.send(**res,ephemeral=True,wait=True,silent=True)
                await MemberManagerBot.output_log(ctx.guild,log)

                try:
                    await asyncio.sleep(ctx.extras.get('wait_time',60))
                    await message.delete()
                except Exception as e:
                    pass

        return wrapper

    async def media_mgt_interest_auto(self,interaction:discord.Interaction,current:str) -> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=value['emoji']+value['label'],value=key) for key,value in self.DATA[str(interaction.guild.id)].interests.items() if
            (value['label'].startswith(current) or value['emoji'].startswith(current) or key.startswith(current))
            ]




    # コマンド:チャンネル設定✅ !B
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
    @command_checker
    async def media_mgt_set_channel(
            self,
            ctx:discord.Interaction,
            channel_type:discord.app_commands.Choice[str],
            channel:discord.TextChannel=None
    ):
        guild_data : GuildData = ctx.extras['data']

        ctx.extras['process'] = '入力確認'
        if (type(channel_type) is not discord.app_commands.models.Choice) and (channel_type.value not in ['join','update','interest','log','year_counter','member_counter']):
            raise InputError('channel_type')
        if channel is None:
            channel = ctx.channel

        ctx.extras['process'] = '埋め込みメッセージ送信'
        message : discord.Message = None
        if (channel_type.value == 'join'):
            message = await channel.send(**self.JoinWidget.Start())
        elif (channel_type.value == 'update'):
            message = await channel.send(**self.UpdateWidget.Start())
        elif (channel_type.value == 'interest'):
            message = await channel.send(**self.InterestWidget.Start(ctx.guild))

        ctx.extras['process'] = 'データ更新'
        guild_data.channels[channel_type.value] = {
            'channel':channel.id,
            'message':message.id if message is not None else None
        }
        guild_data.save_channel_data()

        ctx.extras['process'] = '出力'
        msg = f'{channel_type.name}を<#{channel.id}>に設定しました'
        res = {'content':msg}
        log = self.generate_command_log_embed(ctx,msg)

        return res,log


    @discord.app_commands.command(name='media_mgt_set_category',description='カテゴリを設定します')
    @discord.app_commands.choices(
        category_type = [
            discord.app_commands.Choice(name='創作活動カテゴリ',value='creation'),
            discord.app_commands.Choice(name='非表示カテゴリ',value='hidden'),
        ]
    )
    @discord.app_commands.describe(category_type='カテゴリの種類')
    @discord.app_commands.describe(category='対象カテゴリ. 省略時は現在のチャンネルが属するカテゴリ')
    @command_checker
    async def media_mgt_set_category(
            self,
            ctx:discord.Interaction,
            category_type:discord.app_commands.Choice[str],
            category:discord.CategoryChannel=None
    ):
        guild_data : GuildData = ctx.extras['data']

        ctx.extras['process'] = '入力確認'
        if (type(category_type) is not discord.app_commands.models.Choice):
            raise InputError('category_type')
        elif (category_type.value not in ['creation','hidden']):
            raise InputError('category_type')

        if category is None:
            category = ctx.channel.category
        elif (type(category) is not discord.CategoryChannel):
            raise InputError('category')

        ctx.extras['process'] = 'データ更新'
        guild_data.channels[category_type.value] = {
            'channel': category.id,
            'message': None
        }
        guild_data.save_channel_data()

        ctx.extras['process'] = '出力'
        msg = f'{category_type.name}を<#{category.id}>に設定しました'
        res = {'content':msg}
        log = self.generate_command_log_embed(ctx,msg)

        return res,log


    # コマンド:データ編集 !B
    @discord.app_commands.command(name='media_mgt_view_mydata',description='自身の情報を表示します')
    @command_checker
    async def media_mgt_view_mydata(self,ctx:discord.Interaction):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(ctx.user.id))
        if member_data is None:
            raise NoMemberError(ctx.user.name)

        member_data = self.check_member_data(ctx.guild,member_data)
        if member_data is None:
            raise NoMemberError(ctx.user.name)


        ctx.extras['process'] = '埋め込みメッセージ送信'
        embed = discord.Embed(
            title=f'{ctx.user.name}さんの情報',
            description='データベースに登録されている情報を表示します',
            color=0x00ff00,
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.user.name,icon_url=ctx.user.avatar.url)
        embed.add_field(name='メンバー情報',value=self.member_data_to_code(guild_data.interests,member_data))


        ctx.extras['process'] = '出力'
        return {'embed':embed},self.generate_command_log_embed(ctx,'ユーザーの情報を表示しました')



    @discord.app_commands.command(name='media_mgt_view_member',description='メンバーの情報を表示します')
    @discord.app_commands.describe(member='対象のユーザー')
    @command_checker
    async def media_mgt_view_member(self,ctx:discord.Interaction,member:discord.Member):
        guild_data = self.DATA[str(ctx.guild.id)]

        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')

        ctx.extras['process'] = 'ユーザー確認'
        data = guild_data.members.get(str(member.id))
        if data is None:
            raise NoMemberError(member.name)
        data = self.check_member_data(ctx.guild,data)
        if data is None:
            raise NoMemberError(member.name)

        ctx.extras['process'] = '埋め込みメッセージ送信'
        embed = discord.Embed(
            title=f'{member.name}さんの情報',
            description='データベースに登録されている情報を表示します',
            color=0x00ff00,
            timestamp=datetime.datetime.now()
        )
        embed.set_author(name=member.name,icon_url=member.avatar.url)
        embed.add_field(name='メンバー情報',value=self.member_data_to_code(guild_data.interests,data))

        ctx.extras['process'] = '出力'
        return {'embed':embed},self.generate_command_log_embed(ctx,'ユーザーの情報を表示しました')


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
    @command_checker
    async def media_mgt_set_rank(
            self,
            ctx:discord.Interaction,
            member:discord.Member,
            rank:discord.app_commands.Choice[str]
    ):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')

        if (type(rank) is not discord.app_commands.models.Choice):
            raise InputError('rank')
        elif (rank.value not in ['visitor','member','staff','admin','retirement','consultant']):
            raise InputError('rank')


        ctx.extras['process'] = 'ユーザー確認'
        if (guild_data.members.get(str(member.id)) is None):
            raise NoMemberError(member.name)
        if (guild_data.members.get(str(ctx.user.id)) is None):
            raise NoMemberError(ctx.user.name)
        data = guild_data.members.get(str(member.id),{})


        ctx.extras['process'] = 'ランク照合'
        self.check_member_rank_editable(ctx.user,member,rank.value)


        ctx.extras['process'] = 'メンバー情報更新'
        data['rank'] = rank.value
        await self.set_member_data(member,data)


        ctx.extras['process'] = '出力'
        res = {'content':'メンバーのランクを設定しました'}
        log = self.generate_command_log_embed(ctx,'メンバーのランクを設定しました')
        log['embed'].add_field(name='メンバー情報',value=self.member_data_to_code(guild_data.interests,data))

        return res,log



    @discord.app_commands.command(name='media_mgt_set_interest',description='メンバーの興味を設定します')
    @discord.app_commands.autocomplete(interest=media_mgt_interest_auto)
    @discord.app_commands.describe(member='対象のユーザー')
    @discord.app_commands.describe(mode='設定方法')
    @discord.app_commands.describe(interest='班')
    @command_checker
    async def media_mgt_set_interest(self,ctx:discord.Interaction,member:discord.Member,mode:bool,interest:str):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')

        if (type(mode) is not bool):
            raise InputError('mode')

        if (type(interest) is not str):
            raise InputError('interest')
        elif (interest not in guild_data.interests.keys()):
            raise InputError('interest')


        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(member.id))
        if member_data is None:
            raise NoMemberError(member.name)


        ctx.extras['process'] = 'メンバー情報更新'
        member_data = guild_data.members.get(str(member.id),{})
        if mode:
            member_data['interest'].append(interest)
        else:
            member_data['interest'].remove(interest)
        await self.set_member_data(member,member_data)


        ctx.extras['process'] = '出力'

        res = {'content':'メンバーの興味を設定しました'}
        log = self.generate_command_log_embed(ctx,'メンバーの興味を設定しました')

        await res,log




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
    @command_checker
    async def media_mgt_edit_member(
            self,
            ctx:discord.Interaction,
            member:discord.Member,
            name:str = None,
            rank:discord.app_commands.Choice[str] = None,
            grade:discord.app_commands.Choice[str] = None,
            course:discord.app_commands.Choice[str] = None
    ):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')

        if (type(name) is not str) and (name is not None):
            raise InputError('name')

        if (type(rank) is not discord.app_commands.models.Choice) and (rank is not None):
            raise InputError('rank')
        elif (rank.value not in ['visitor','member','staff','admin','retirement','consultant']):
            raise InputError('rank')

        if (type(grade) is not discord.app_commands.models.Choice) and (grade is not None):
            raise InputError('grade')
        elif (grade.value not in ['graduation','special','grade1','grade2','grade3','grade4','grade5']):
            raise InputError('grade')

        if (type(course) is not discord.app_commands.models.Choice) and (course is not None):
            raise InputError('course')
        elif (course.value not in ['class5','class6','class7','class8','courseT','courseA','courseR','courseW']):
            raise InputError('course')

        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(member.id))
        if member_data is None:
            raise NoMemberError(member.name)


        ctx.extras['process'] = 'ランク照合'
        self.check_member_rank_editable(ctx.user,member,rank.value if (rank is not None) else None)


        ctx.extras['process'] = 'メンバー情報更新'
        data = {
            'name':name if (name is not None) else member_data.get('name'),
            'rank':rank.value if (rank is not None) else member_data.get('rank'),
            'grade':grade.value if (grade is not None) else member_data.get('grade'),
            'course':course.value if (course is not None) else member_data.get('course'),
            'interest':guild_data.members.get(str(member.id),{}).get('interest',[]).copy(),
            'stop_count':0,
            'lock':0
        }
        flag = await self.set_member_data(member,data)


        ctx.extras['process'] = '出力'
        if flag:
            return {'content':'メンバー情報を編集しました'},self.generate_command_log_embed(ctx,'メンバー情報を編集しました')
        else:
            return {'content':'メンバー情報を編集できません'},self.generate_command_failed_log_embed(ctx,FailedMemberEditError(member.name),'メンバー情報を編集できません')





    @discord.app_commands.command(name='media_mgt_clear_member',description='メンバーのデータをクリアします')
    @discord.app_commands.describe(member='対象メンバー')
    @command_checker
    async def media_mgt_clear_member(self,ctx:discord.Interaction,member:discord.Member):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')


        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(member.id))
        if member_data is None:
            raise NoMemberError(member.name)


        ctx.extras['process'] = 'メンバー情報更新'
        flag = await self.clear_member_data(member)


        ctx.extras['process'] = '出力'
        if flag:
            return {'content':'メンバー情報をクリアしました'},self.generate_command_log_embed(ctx,'メンバー情報をクリアしました')
        else:
            return {'content':'メンバー情報をクリアできません'},self.generate_command_failed_log_embed(ctx,FailedMemberEditError(member.name),'メンバー情報をクリアできません')



    @discord.app_commands.command(name='media_mgt_member_suspension',description='メンバーを一時停止します')
    @discord.app_commands.describe(member='対象メンバー')
    @discord.app_commands.describe(duration='停止時間(日)')
    @discord.app_commands.describe(reason='停止理由')
    @command_checker
    async def media_mgt_member_suspension(self,ctx:discord.Interaction,member:discord.Member,duration:int,reason:str = None):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')

        if (type(duration) is not int):
            raise InputError('duration')

        if reason is None:
            reason = '不明'
        elif (type(reason) is not str):
            raise InputError('reason')


        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(member.id))
        if member_data is None:
            raise NoMemberError(member.name)

        ctx.extras['process'] = 'ランク照合'
        self.check_member_rank_editable(ctx.user,member,'member')

        ctx.extras['process'] = 'メンバー情報更新'
        member_data['lock'] = int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'))+duration
        await self.set_member_data(member,member_data)

        ctx.extras['process'] = '出力'
        return {'content':'メンバーを一時停止しました'},self.generate_command_log_embed(ctx,'メンバーを一時停止しました')


    @discord.app_commands.command(name='media_mgt_release_member',description='メンバーの一時停止を解除します')
    @discord.app_commands.describe(member='対象メンバー')
    @command_checker
    async def media_mgt_release_member(self,ctx:discord.Interaction,member:discord.Member):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = '入力確認'
        if (type(member) is not discord.Member):
            raise InputError('member')


        ctx.extras['process'] = 'ユーザー確認'
        member_data = guild_data.members.get(str(member.id))
        if member_data is None:
            raise NoMemberError(member.name)


        ctx.extras['process'] = 'ランク照合'
        self.check_member_rank_editable(ctx.user,member,'member')


        ctx.extras['process'] = 'メンバー情報更新'
        member_data['lock'] = 0
        self.set_member_data(member,member_data)


        ctx.extras['process'] = '出力'
        return {'content':'メンバーの一時停止を解除しました'},self.generate_command_log_embed(ctx,'メンバーの一時停止を解除しました')




    # コマンド:班設定 !B

    @discord.app_commands.command(name='media_mgt_add_interest',description='班を追加します')
    @discord.app_commands.describe(label='名前')
    @discord.app_commands.describe(value='内部識別子')
    @discord.app_commands.describe(emoji='絵文字')
    @discord.app_commands.describe(role='対応するロール')
    @discord.app_commands.describe(channel='対応するチャンネル')
    @command_checker
    async def media_mgt_add_interest(
        self,
        ctx:discord.Interaction,
        label:str,
        value:str,
        emoji:str,
        role:discord.Role = None,
        channel:discord.TextChannel = None
    ):
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = 'カテゴリ情報取得'
        category = self.get_category_data(ctx.guild,'creation')
        if category is None:
            raise NoChannelError('所属班カテゴリ')


        ctx.extras['process'] = '入力確認'
        if (type(label) is not str):
            raise InputError('label')
        elif (label in [interest['label'] for interest in guild_data.interests.values()]):
            raise InputError('label')

        if (type(value) is not str):
            raise InputError('value')
        elif (value in guild_data.interests.keys()):
            raise InputError('value')

        if (type(emoji) is not str):
            raise InputError('emoji')
        elif (emoji.replace('︎','').replace('️','') in [interest['emoji'].replace('︎','').replace('️','') for interest in guild_data.interests.values()] and (not is_emoji(emoji))):
            raise InputError('emoji')
        emoji = emoji.replace('︎','').replace('️','') + '️'

        if (type(role) is not discord.Role) and (role is not None):
            raise InputError('role')

        if (type(channel) is not discord.TextChannel) and (channel is not None):
            raise InputError('channel')


        ctx.extras['process'] = 'ロール操作'
        index = min([ctx.guild.get_role(i['role_id']).position for i in guild_data.interests.values()]+[1])
        if (role is None):
            role = await ctx.guild.create_role(name=label)
            await role.edit(position=index,color=guild_data.parameters.get('interest_color',0))
        else:
            await role.edit(name=label,position=index,color=guild_data.parameters.get('interest_color',0),permissions=discord.Permissions.none())


        ctx.extras['process'] = 'チャンネル操作'
        index = max([i.position for i in category.text_channels]+[1])
        if (channel is None):
            channel = await ctx.guild.create_text_channel(emoji+label,category=category,position=index,slowmode_delay=1)
        else:
            await channel.edit(name=emoji+label,category=category,position=index,slowmode_delay=1)
        
        await self.sync_permission(channel)
        
        overwrite = discord.PermissionOverwrite()
        overwrite.create_public_threads = True
        overwrite.create_private_threads = True
        
        await channel.set_permissions(role,overwrite=overwrite)

            
        ctx.extras['process'] = '班情報更新'
        data : interestData = {
            'label':label,
            'emoji':emoji,
            'role_id':role.id,
            'channel_id':channel.id
        }
        guild_data.interests[value] = data
        guild_data.save_interest_data()


        ctx.extras['process'] = '更新処理'
        await self.resend_widget(ctx.guild,'interest')
        await self.apply_all_member(ctx.guild)


        ctx.extras['process'] = '出力'
        res = {'content':'班を追加しました'}
        log = self.generate_command_log_embed(ctx,'班を追加しました')
        log['embed'].add_field(name='班情報',value=self.interest_data_to_code(value,data),inline=True)

        return res,log




    @discord.app_commands.command(name='media_mgt_edit_interest',description='班を編集します')
    @discord.app_commands.autocomplete(interest=media_mgt_interest_auto)
    @discord.app_commands.describe(interest='対象班')
    @discord.app_commands.describe(label='名前')
    @discord.app_commands.describe(value='内部識別子')
    @discord.app_commands.describe(emoji='絵文字')
    @discord.app_commands.describe(role='対応するロール')
    @discord.app_commands.describe(channel='対応するチャンネル')
    @command_checker
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
        guild_data : GuildData = ctx.extras['data']


        ctx.extras['process'] = 'カテゴリ情報取得'
        creation_category = self.get_category_data(ctx.guild,'creation')
        if creation_category is None:
            raise NoChannelError('所属班カテゴリ')

        hidden_category = self.get_category_data(ctx.guild,'hidden')
        if hidden_category is None:
            raise NoChannelError('非表示カテゴリ')


        ctx.extras['process'] = '入力確認'
        current = guild_data.interests.get(interest)
        if (current is None):
            raise InputError('interest')

        if label is None:
            label = current['label']
        elif (type(label) is not str):
            raise InputError('label')
        elif (label in [interest['label'] for interest in guild_data.interests.values()]):
            raise InputError('label')

        if value is None:
            value = interest
        elif (type(value) is not str):
            raise InputError('value')
        elif (value in guild_data.interests.keys()):
            raise InputError('value')

        if emoji is None:
            emoji = current['emoji']
        elif (type(emoji) is not str):
            raise InputError('emoji')
        elif (emoji.replace('︎','').replace('️','') in [interest['emoji'].replace('︎','').replace('️','') for interest in guild_data.interests.values()] and (not is_emoji(emoji))):
            raise InputError('emoji')
        emoji = emoji.replace('︎','').replace('️','') + '️'

        if (type(role) is not discord.Role) and (role is not None):
            raise InputError('role')

        if (type(channel) is not discord.TextChannel) and (channel is not None):
            raise InputError('channel')


        ctx.extras['process'] = 'ロール操作'
        index = min([ctx.guild.get_role(i['role_id']).position for i in guild_data.interests.values()])
        if (role is None):
            role = ctx.guild.get_role(current['role_id'])
        else:
            before_role = ctx.guild.get_role(current['role_id'])
            await before_role.delete()
        await role.edit(name=label,color=guild_data.parameters.get('interest_color',0),position=index,permissions=discord.Permissions.none())


        ctx.extras['process'] = 'チャンネル操作'
        if (channel is None):
            channel = ctx.guild.get_channel(current['channel_id'])
        else:
            before_channel = ctx.guild.get_channel(current['channel_id'])
            await before_channel.edit(category=hidden_category)
            await self.sync_permission(before_channel)

        await channel.edit(name=emoji+label,category=creation_category,position=index,slowmode_delay=1)
        await self.sync_permission(channel)

        overwrite = discord.PermissionOverwrite()
        overwrite.create_public_threads = True
        overwrite.create_private_threads = True

        await channel.set_permissions(role,overwrite=overwrite)


        ctx.extras['process'] = '班情報更新'
        before_data = guild_data.interests[interest]
        del guild_data.interests[interest]

        data : interestData = {
            'label':current['label'] if label is None else label,
            'emoji':current['emoji'] if label is None else emoji,
            'channel_id':current['channel_id'] if label is None else channel.id,
            'role_id':current['role_id'] if role is None else role.id
        }
        guild_data.interests[value] = data
        guild_data.save_interest_data()


        ctx.extras['process'] = '更新処理'
        for key,val in guild_data.members.items():
            try:
                interests = [value if i == interest else i for i in val.get('interest',[])]
                if (interests != val.get('interest',[])):
                    guild_data.members[key]['interest'] = interests
            except:
                pass
        await self.apply_all_member(ctx.guild)

        await self.resend_widget(ctx.guild,'interest')


        ctx.extras['process'] = '出力'
        res = {'content':'班を編集しました'}
        log = self.generate_command_log_embed(ctx,'班を編集しました')
        log['embed'].add_field(name='変更前',value=self.interest_data_to_code(interest,before_data),inline=True)
        log['embed'].add_field(name='変更後',value=self.interest_data_to_code(value,data),inline=True)

        return res,log



    @discord.app_commands.command(name='media_mgt_remove_interest',description='班を削除します')
    @discord.app_commands.autocomplete(interest=media_mgt_interest_auto)
    @discord.app_commands.describe(interest='対象班')
    @command_checker
    async def media_mgt_remove_interest(self,ctx:discord.Interaction,interest:str):
        guild_data : GuildData = ctx.extras['data']



        ctx.extras['process'] = 'カテゴリ情報取得'
        hidden_category = self.get_category_data(ctx.guild,'hidden')
        if hidden_category is None:
            raise NoChannelError('非表示カテゴリ')


        ctx.extras['process'] = '入力確認'
        current = guild_data.interests.get(interest)
        if (current is None):
            raise InputError('interest')


        ctx.extras['process'] = 'ロール操作'
        role = ctx.guild.get_role(current['role_id'])
        await role.delete()

        ctx.extras['process'] = 'チャンネル操作'
        channel = ctx.guild.get_channel(current['channel_id'])
        await channel.edit(category=hidden_category)
        await self.sync_permission(channel)


        ctx.extras['process'] = '班情報更新'
        del guild_data.interests[interest]
        guild_data.save_interest_data()


        ctx.extras['process'] = '更新処理'
        await self.resend_widget(ctx.guild,'interest')
        await self.apply_all_member(ctx.guild)


        ctx.extras['process'] = '出力'
        res = {'content':'班を削除しました'}
        log = self.generate_command_log_embed(ctx,'班を削除しました')
        log['embed'].add_field(name='班情報',value=self.interest_data_to_code(interest,current),inline=True)

        return res,log



    @discord.app_commands.command(name='test_command',description='テストコマンド.使用禁止')
    @command_checker
    async def test_command(self,ctx:discord.Interaction):
        guild_data = self.DATA[str(ctx.guild.id)]

        embed = discord.Embed(title='デバッグボタン')
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='CMD1',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_command1'))
        view.add_item(discord.ui.Button(label='CMD2',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_command2'))
        view.add_item(discord.ui.Button(label='CMD3',style=discord.ButtonStyle.red,custom_id='media_mgt_debug_command3'))
        view.add_item(discord.ui.Button(label='CMD4',style=discord.ButtonStyle.grey,custom_id='media_mgt_debug_command4'))
        view.add_item(discord.ui.Button(label='CMD5',style=discord.ButtonStyle.grey,custom_id='media_mgt_debug_command5'))
        message = await ctx.channel.send(embed=embed,view=view)
        guild_data.channels['debug'] = {
            'channel' : message.channel.id,
            'message' : message.id
        }
        guild_data.save_channel_data()
        await ctx.response.send_message('テストコマンドを実行しました',ephemeral=True)


    @discord.app_commands.command(name='test_command2',description='テストコマンド2.使用禁止')
    @command_checker
    async def test_command2(self,ctx:discord.Interaction):
        embed = discord.Embed(title='仮設パネル',description='簡易的に設定を変更できます')

        embed.add_field(name='現役の会員さんへ',value='青い「リセット」と書かれたボタンを押してください。\nその後は入会手続きチャンネルが表示されるはずなので指示に従って入力して下さい\n近日中に会員ロールを付与します',inline=False)
        embed.add_field(name='卒業生の方々へ',value='緑のボタンでコースを変更できます。\n赤いボタンを押すと名前を変更できます',inline=False)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='リセット',style=discord.ButtonStyle.blurple,custom_id='media_mgt_debug_reset',row=0))
        view.add_item(discord.ui.Button(label='情報通信',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_courseT',row=1))
        view.add_item(discord.ui.Button(label='ロボット',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_courseR',row=1))
        view.add_item(discord.ui.Button(label='航空宇宙',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_courseA',row=1))
        view.add_item(discord.ui.Button(label='医療福祉',style=discord.ButtonStyle.green,custom_id='media_mgt_debug_courseW',row=1))
        view.add_item(discord.ui.Button(label='名前変更',style=discord.ButtonStyle.red,custom_id='media_mgt_debug_name',row=1))

        message = await ctx.channel.send(embed=embed,view=view)



    # 関数

    # 関数:ロード/セーブ !B
    @classmethod
    async def load_channels(cls,guild:discord.Guild):
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
                m = await cls.get_message_data(guild,i)
                result[i] = m is not None
            except:
                pass

        for i in list(['log','year_counter','member_counter']):
            try:
                result[i] = cls.get_channel_data(guild,i) is not None
            except:
                pass

        for i in list(['creation','hidden']):
            try:
                result[i] = cls.get_category_data(guild,i) is not None
            except:
                pass

        return result

    # 関数:ロールデータ
    @classmethod
    async def sync_permission(cls,channel:discord.TextChannel):
        try:
            category = channel.category
            for obj in channel.overwrites.keys():
                if obj not in category.overwrites.keys():
                    await channel.set_permissions(obj,overwrite=None)
                    await asyncio.sleep(0.2)
            
            for key,value in category.overwrites.items():
                await channel.set_permissions(key,overwrite=value)
                await asyncio.sleep(0.2)
            
        except Exception as e:
            print(e)
            return None

    # 関数:チャンネルデータ✅ !B
    @classmethod
    async def get_message_data(cls,guild:discord.Guild,widget:typing.Literal['join','update','interest']):
        try:
            data = cls.DATA[str(guild.id)]
            channel = guild.get_channel(data.channels.get(widget,{}).get('channel'))
            message = await channel.fetch_message(data.channels.get(widget,{}).get('message'))
            return message
        except:
            return None

    @classmethod
    def get_channel_data(cls,guild:discord.Guild,ch:typing.Literal['log','member_counter','year_counter']):
        try:
            data = cls.DATA[str(guild.id)]
            channel = guild.get_channel(data.channels.get(ch,{}).get('channel'))
            return channel
        except:
            return None

    @classmethod
    def get_category_data(cls,guild:discord.Guild,ch:typing.Literal['creation','hidden']):
        try:
            data = cls.DATA[str(guild.id)]
            category = guild.get_channel(data.channels.get(ch,{}).get('channel'))
            return category
        except:
            return None



    @classmethod
    async def resend_widget(cls,guild:discord.Guild,widget:typing.Literal['join','update','interest']) -> bool:
        try:
            message = await cls.get_message_data(guild,widget)
            if message is None:
                return False

            if widget == 'join':
                await message.edit(**cls.JoinWidget.Start())
            elif widget == 'update':
                await message.edit(**cls.UpdateWidget.Start())
            elif widget == 'interest':
                await message.edit(**cls.InterestWidget.Start(guild))

            return True
        except:
            return False


    # 関数:メンバーデータ編集 !B
    @classmethod
    def check_member_rank_editable(cls,from_member:discord.Member,to_member:discord.Member,val:RANK = None):
        class RankValueError(FaildError):
            def __init__(self,message:str):
                self.arg = message

            def __str__(self):
                return self.arg

        if (from_member.guild.id != to_member.guild.id):
            raise MemberDataError('実行者と対象者のサーバーが異なります')
        data = cls.DATA[str(from_member.guild.id)]

        from_rank = data.members.get(str(from_member.id),{}).get('rank')
        to_rank   = data.members.get(str(to_member.id),{}).get('rank')
        ranks = ['visitor','member','staff','admin','retirement','consultant','owner']

        if from_rank not in ranks:
            raise MemberDataError('実行者のランクが取得できません')
        elif to_rank not in ranks:
            raise MemberDataError('対象者のランクが取得できません')
        elif (val not in ranks and val is not None):
            raise InputError('rank')


        from_val = int(data.role_tags['rank'].get(from_rank,{}).get('value',0))
        to_val   = int(data.role_tags['rank'].get(to_rank,{}).get('value',0))
        val_val  = int(data.role_tags['rank'].get(val,{}).get('value',0))

        if from_val <= to_val:
            raise RankValueError(f'対象は実行者より低いランクのユーザーである必要があります:{from_val}/{to_val}')
        if from_val <= val_val and val is not None:
            raise RankValueError(f'実行者より低いランクしか付与できません:{from_val}/{val_val}')

    @classmethod
    def check_member_data(cls,guild:discord.Guild,data:memberData) -> typing.Union[memberData,None]:
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
            'interest':sorted(list(set([str(i) for i in data.get('interest',[]) if i in cls.DATA.get(str(guild.id)).interests.keys()]))),
            'stop_count': data.get('stop_count',0) if (type(data.get('stop_count',0)) is int) else 0,
            'lock': data.get('lock',0) if (type(data.get('lock',0)) is int) else 0
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
        guild_data = cls.DATA[str(member.guild.id)]

        if (type(member) is not discord.Member):
            return False

        # ロールの更新
        add_roles = []
        remove_roles = [role for role in member.roles if (str(role.id) in list(guild_data.roles.keys())+[str(interest['role_id']) for interest in guild_data.interests.values()])]

        add_roles_id = []
        if (data is None):
            pass
        elif (data['lock'] > int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d'))):
            add_roles_id.append(guild_data.role_tags.get('special_rank',{}).get('lock',{}).get('role_id',0))
            pass
        elif (data['stop_count'] > 0):
            add_roles_id.append(guild_data.role_tags.get('special_rank',{}).get('stop',{}).get('role_id',0))
        else:
            add_roles_id.append(guild_data.role_tags.get('rank',{}).get(data['rank'],{}).get('role_id',0))
            add_roles_id.append(guild_data.role_tags.get('grade',{}).get(data['grade'],{}).get('role_id',0))
            add_roles_id.append(guild_data.role_tags.get('course',{}).get(data['course'],{}).get('role_id',0))
            for role in data['interest']:
                add_roles_id.append(guild_data.interests.get(role,{}).get('role_id',0))

        add_roles = [member.guild.get_role(role_id) for role_id in add_roles_id]

        remove_roles = [role for role in remove_roles if (role not in add_roles   ) and (role is not None)]
        add_roles    = [role for role in add_roles    if (role not in member.roles) and (role is not None)]

        if (len(remove_roles) > 0):
            print('remove',member.id,remove_roles)
            await member.remove_roles(*remove_roles)
        if (len(add_roles) > 0):
            print('add',member.id,add_roles)
            await member.add_roles(*add_roles)

        return True

    @classmethod
    async def set_member_name(cls,member:discord.Member,data:memberData = None):
        name = ''

        if (data is None):
            name = None
        else:
            if (data['lock'] > (d:=int(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d')))):
                val = '999+' if data['lock'] - d > 999 else str(data['lock'] - d)
                name = data['name'] + f'_残り{val}日'
            elif (data['stop_count'] > 0):
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

                name += data['name'][:24]

                for interest in data['interest']:
                    name += str(cls.DATA[str(member.guild.id)].interests.get(interest,{}).get('emoji',''))
                name = name.replace('︎','').replace('️','')

        if member.guild.owner_id != member.id :
            if member.nick != name:
                print(member.nick,name)
                await member.edit(nick=name)
        pass


    @classmethod
    async def set_member_data(cls,member:discord.Member,data:memberData = None ,*, is_save:bool=True) -> bool:
        guild_data = cls.DATA[str(member.guild.id)]

        member_id = member.id
        if (data is None):
            data = guild_data.members.get(str(member_id),{})
        if (type(member) is not discord.Member):
            return False

        mold = cls.check_member_data(member.guild,data)
        if (mold is None):
            return False


        # リストの更新
        guild_data.members[str(member_id)] = mold
        if is_save: guild_data.save_member_data()

        # ロールの更新
        await cls.set_member_role(member,mold)


        # ニックネームの更新
        await MemberManagerBot.set_member_name(member,mold)

        return True

    @classmethod
    async def clear_member_data(cls,member:discord.Member):
        guild_data = cls.DATA[str(member.guild.id)]

        if (type(member) is not discord.Member):
            return False
        if (str(member.id) not in guild_data.members.keys()):
            return False

        del guild_data.members[str(member.id)]
        guild_data.save_member_data()

        await cls.set_member_role(member)
        await cls.set_member_name(member)
        return True


    @classmethod
    async def apply_all_member(cls,guild:discord.Guild):
        print('apply_all_member')
        guild_data = cls.DATA[str(guild.id)]

        new_member_list : typing.Dict[str,memberData] = {}

        for member in guild.members:
            try:
                if guild.owner == member:
                    data = cls.check_member_data(guild,{'rank':'owner','name':'サーバー管理'})
                    await cls.set_member_role(member,data)
                    new_member_list[str(member.id)] = data

                elif str(member.id) in guild_data.members.keys():
                    data = cls.check_member_data(guild,guild_data.members[str(member.id)])
                    await cls.set_member_role(member,data)
                    await cls.set_member_name(member,data)
                    if data is None : raise
                    new_member_list[str(member.id)] = data
                else:
                    await cls.set_member_role(member)
                    await cls.set_member_name(member)

            except Exception as e:
                print(e)
                pass
            finally:
                await asyncio.sleep(0.2)


        guild_data.members = new_member_list
        guild_data.save_member_data()

    @classmethod
    async def renewal_all_member(cls,guild:discord.Guild,year:int=1):
        data = cls.DATA[str(guild.id)]
        for member_id in data.members.keys():
            try:
                data.members[member_id]['stop_count'] += year
            except:
                pass
        await cls.apply_all_member(guild)


    # 関数:統計更新 !B
    @classmethod
    async def update_year_counter(cls,guild:discord.Guild):
        data = cls.DATA[str(guild.id)]
        ch = guild.get_channel(data.channels.get('year_counter',{}).get('channel',0))
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
                await cls.renewal_all_member(guild,v-val)
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
    async def update_member_counter(cls,guild:discord.Guild):
        data = cls.DATA[str(guild.id)]

        ch = guild.get_channel(data.channels.get('member_counter',{}).get('channel',0))
        if ch is None:
            return

        try:
            name = ch.name
            val = int(re.search(r'\d+',name).group())

            v = 0
            for member in data.members.values():
                if member['rank'] in ['member','staff','admin']:
                    v += 1

            if v != val:
                await ch.edit(name=name.replace(str(val),str(v)))
        except:
            pass


    # 関数:変換 !B
    @classmethod
    def member_data_to_code(cls,interests,data:memberData):
        rank_label = {
            'visitor':'見学',
            'member':'会員',
            'staff':'幹部',
            'admin':'会長',
            'retirement':'卒業生',
            'consultant':'顧問',
            'owner':'管理者'
        }

        grade_label = {
            'graduation':'OB・OG',
            'special':'専攻科',
            'grade1':'1年',
            'grade2':'2年',
            'grade3':'3年',
            'grade4':'4年',
            'grade5':'5年',
        }

        course_label = {
            'courseT':'情報通信工学コース',
            'courseR':'ロボット工学コース',
            'courseA':'航空宇宙工学コース',
            'courseW':'医療福祉工学コース',
            'class5':'5組',
            'class6':'6組',
            'class7':'7組',
            'class8':'8組',
        }

        text = ''
        text += f'名　前：{data.get("name")}\n'
        text += f'ランク：{rank_label.get(data.get("rank"),'----')}\n'
        text += f'学　年：{grade_label.get(data.get("grade"),'----')}\n'
        text += f'コース：{course_label.get(data.get("course"),'----')}\n'
        text += f'所属班：' + '\n　　　　'.join([f'{interests.get(i,{}).get("emoji")}{interests.get(i,{}).get("label")}' for i in data.get('interest',[])])
        return f'```ansi\n[1;2m[0m[2;37m[1;37m{text}\n```'

    @classmethod
    def interest_data_to_code(cls,value,data:interestData):
        text = ''
        text += f'名　前：{data.get("label")}\n'
        text += f'識別子：{value}\n'
        text += f'絵文字：{data.get("emoji")}\n'
        text += f'ロール：{data.get("role_id")}\n'
        text += f'チャンネル:{data.get("channel_id")}\n'
        return f'```ansi\n[1;2m[0m[2;37m[1;37m{text}\n```'



    # 関数:ログ !B
    @classmethod
    async def output_log(cls,guild:discord.Guild,data):
        guild_data = cls.DATA[str(guild.id)]
        if guild_data.channels.get('log',{}).get('channel') is None:
            return
        await cls.Bot.get_channel(guild_data.channels['log']['channel']).send(**data)



    @staticmethod
    async def generete_load_log_embed(guild:discord.Guild,load_data:dict):
        file_log = ''
        for k,v in load_data.items():
            file_log += f'[2;33m{k: <12}[2;37m:[0m[2;33m[0m{'[2;32m[1;32m成功[0m[2;32m[0m' if v else '[2;31m[1;31m失敗[0m[2;31m[0m'}\n'
            pass

        channel_log = ''


        result = await MemberManagerBot.load_channels(guild)
        for key,value in result.items():
            flag = value
            channel_log += f'[2;33m{key: <8}[2;37m:[0m[2;33m[0m{'[2;32m[1;32m接続成功[0m[2;32m[0m' if flag else '[2;31m[1;31m失敗[0m[2;31m[0m'}\n'


        embed = discord.Embed(title='ロード完了',description='ボットが起動しました',color=discord.Color.green())
        embed.add_field(name='ファイルロード',value=f'```ansi\n{file_log}```',inline=False)
        embed.add_field(name='チャンネルロード',value=f'```ansi\n{channel_log}```',inline=False)
        return {'embed':embed}

    @classmethod
    def generate_edit_member_log_embed(cls,reason:str,user:discord.User,before:memberData,after:memberData):

        embed = discord.Embed(
            title='メンバー情報が編集されました',
            description=f'<@{user.id}>',
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
        embed.set_author(name = 'メンバー変更ログ')


        text_generator = lambda member_data: '```ansi\n'\
            f'名　前 : {member_data.get("name")}\n'\
            f'ランク : {member_data.get("rank")}\n'\
            f'学　年 : {member_data.get("grade")}\n'\
            f'コース : {member_data.get("course")}\n'\
            f'所　属 : {member_data.get("interest")}\n'\
            f'更新値 : {member_data.get("stop_count")}\n```'\

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
    def generate_command_failed_log_embed(cls,ctx:discord.Interaction,error_data:Exception,description:str = 'None'):
        inputs = [f'{key}:{value}' for key,value in ctx.namespace.__dict__.items()]

        embed = discord.Embed(
            title='コマンド実行失敗ログ',
            description = f'コマンド：{ctx.command.name}\n使用者：<@{ctx.user.id}>\nチャンネル：<#{ctx.channel.id}>',
            color=0xddff99,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        embed.set_author(name = str(error_data.__class__.__name__))
        embed.add_field(name = '入力',value = '```ansi\n'+'\n'.join(inputs if len(inputs)>0 else 'none')+'\n```',inline=False)
        embed.add_field(name = 'エラー詳細',value = str(error_data.args),inline=False)
        embed.add_field(name = '備考',value = description,inline=False)
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


    # デバッグ !B
    @classmethod
    async def debug_resend(cls,guild:discord.Guild):
        try:
            data = cls.DATA[str(guild.id)]

            ch = guild.get_channel(data.channels.get('debug',{}).get('channel',0))
            message = await ch.fetch_message(data.channels.get('debug',{}).get('message',0))

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
