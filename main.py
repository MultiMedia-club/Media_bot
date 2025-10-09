import discord
from discord.ext import tasks
from discord.ext import commands
from discord import app_commands

import asyncio
import glob
import os
import enum
import dotenv
import app.git_push
from app.server import server_thread

dotenv.load_dotenv()

#MTQyNDUxNDE1NzA4Mzg4NTU4OA.GxICBE.wtrR9YpFHq-FEkbnN52Xe4vTTxB3TdJmlXh_C4
#MediaBot
TOKEN='MTQyMzQwNDEyOTM3NTQ4NTk2Mg.GYWt1k.Ry5HnHZp1rJzMVNPq3LraXrRz5FIYXIrZ4er00'

# 環境変数にsourceのパスを登録
os.environ['SOURCE'] = os.path.join(os.path.dirname(__file__),'source')

class CogState(enum.IntEnum):
    ACTIVE   = 0
    LOADING  = 1
    DISABLED = 2
    

class MediaBot(commands.Bot):
    instance = None
    cogs_status = {'media_bot':1}
    git = None

    def __init__(cls):
        super().__init__(command_prefix='!',intents=discord.Intents.all())
        MediaBot.instance = cls
        MediaBot.git = app.git_push.GitPython(
            os.environ['SOURCE'], 
            f'https://{os.environ["GITHUB_TOKEN"]}@github.com/{os.environ["GITHUB_USERNAME"]}/{os.environ["GITHUB_REPOSITORY"]}.git',
            os.environ['GITHUB_USERNAME'],
            os.environ['GITHUB_EMAIL']
        )
        cls.run()

    # Botの起動
    def run(self):
        super().run(os.environ['DISCORD_TOKEN'])


    async def on_ready(self):
        self.hour_loop.start()
        
        # サーバーIDを環境変数に登録
        activity = discord.CustomActivity(name='セットアップ中...')
        await self.change_presence(activity=activity,status=discord.Status.dnd)

        await asyncio.sleep(5)

        # Cog(小分けにした各種機能)の読み込み
        # Cogフォルダ内の.pyファイルの名前をすべて読み込む
        cogs = glob.glob(os.path.join(os.path.dirname(__file__),'cogs','*.py'))

        for cog in cogs:
            if cog == os.path.join(os.path.dirname(__file__),'cogs','__init__.py'):
                continue
            try:
                # ファイル名から拡張子を除いたものを取得して読み込み
                p = os.path.basename(cog).replace('.py', '')

                os.makedirs(os.path.join(os.environ['SOURCE'],p), exist_ok=True)

                MediaBot.cogs_status[p] = False
                await self.load_extension(f'cogs.{p}')


            except Exception as e:
                print(f'Failed to load cog {cog}: {e}')
            await asyncio.sleep(1)

        # コマンドツリーの同期
        await self.tree.sync()

        await self.set_cog_state('media_bot', CogState.ACTIVE)
    
    @tasks.loop(hours=1)
    async def hour_loop(self):
        try:
            self.git.push()
        except:
            pass

    @classmethod
    async def set_cog_state(cls, cog_name:str, state:CogState):
        if cog_name not in cls.cogs_status.keys():
            return
        cls.cogs_status[cog_name] = int(state)

        activity = None
        status = None

        max_status = max(cls.cogs_status.values())
        if max_status == int(CogState.ACTIVE):
            activity = discord.CustomActivity(name='正常に稼働中')
            status = discord.Status.online
        elif max_status == int(CogState.LOADING):
            activity = discord.CustomActivity(name='セットアップ中...')
            status = discord.Status.idle
        else:
            activity = discord.CustomActivity(name='セットアップに失敗しました')
            status = discord.Status.dnd

        await cls.instance.change_presence(activity=activity,status=status)

        

        
server_thread()
bot = MediaBot()
