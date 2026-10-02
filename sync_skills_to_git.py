#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GJC 스킬 깃허브 원클릭 자동 동기화 스크립트 (One-click GitHub Sync)
실행: python C:/Users/imda0/.gjc/agent/skills/sync_skills_to_git.py
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SKILLS_DIR = Path(__file__).resolve().parent


def run_git(cmd: list[str]) -> str:
    res = subprocess.run(["git", "-C", str(SKILLS_DIR)] + cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()


def main():
    print(f"🔄 [GJC Skills] GitHub 자동 동기화 시작: {SKILLS_DIR}")

    # 1. 최신 AGENTS.md 복사
    agents_src = SKILLS_DIR.parent / "AGENTS.md"
    agents_dst = SKILLS_DIR / "AGENTS.md"
    if agents_src.exists():
        import shutil
        shutil.copyfile(agents_src, agents_dst)
        print("✓ AGENTS.md 최신 지침 복사 완료")

    # 2. git add
    run_git(["add", "."])

    # 3. 변경사항 확인
    status = run_git(["status", "--short"])
    if not status:
        print("✅ 변경된 파일이 없습니다. 이미 최신 상태입니다.")
        return 0

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"chore(skills): auto backup skills at {now_str}"

    # 4. commit & push
    run_git(["commit", "-m", commit_msg])
    print(f"✓ 커밋 완료: {commit_msg}")

    print("🚀 GitHub (origin main)으로 푸시 중...")
    run_git(["push", "origin", "main"])
    print("🎉 GitHub 동기화가 성공적으로 완료되었습니다!")
    print("🔗 레포지토리: https://github.com/lsi9923/gjc-skills")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 오류 발생: {e.stderr}", file=sys.stderr)
        sys.exit(1)
