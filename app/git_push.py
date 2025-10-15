import subprocess
import os

class GitPython:
    directory = "."
    git_remote = "origin"
    git_branch = "main"
    remote_url = ""
    status = False

    def __init__(self, directory, remote_url,user,e_mail, git_remote="origin", git_branch="main"):
        self.directory = directory
        self.remote_url = remote_url

        self.user = user
        self.e_mail = e_mail

        self.git_remote = git_remote
        self.git_branch = git_branch

        self.status = self.pull()
        self.set_user()


    def run(self, cmd, cwd=None, check=True):
        """シェルコマンド実行"""
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"[Error] {cmd} failed:\n{result.stderr}")
            raise RuntimeError(result.stderr)
        return result.stdout.strip()


    def set_user(self):
        self.run(["git", "config", "user.name", self.user], cwd=self.directory)
        self.run(["git", "config", "user.email", self.e_mail], cwd=self.directory)


    def pull(self) -> bool:
        # ===== ステップ1: リポジトリ存在確認 =====
        try:
            if not os.path.exists(os.path.join(self.directory, ".git")):
                print("⚙️  リポジトリが存在しません。クローンを実行します。")
                self.run(["git", "clone", self.remote_url, self.directory])
                self.run(["git", "remote", "add", self.git_remote, self.remote_url], cwd=self.directory)
            else:
                print("📁  既存リポジトリを検出。pullを実行します。")
                try:
                    self.run(["git", "pull", self.git_remote, self.git_branch], cwd=self.directory)
                except Exception as e:
                    raise e
            return True
        except Exception as e:
            print("⚠️ pull失敗:", e)
            return False


    def push(self,options=".", commit_message="Auto backup") -> bool:
        # ===== ステップ2: 差分確認 =====
        status = self.run(["git", "status", "--porcelain"], cwd=self.directory)
        try:
            if not status:
                print("✅ 差分なし。バックアップをスキップ。")
            else:
                print("🔄 差分を検出。コミットとpushを実行します。")
                self.run(["git", "add", options], cwd=self.directory)
                self.run(["git", "commit", "-m", commit_message], cwd=self.directory)
                self.run(["git", "push", self.git_remote, self.git_branch], cwd=self.directory)
                print("🚀 バックアップをpushしました。")
            return True
        except Exception as e:
            print("⚠️ push失敗:", e)
            return False