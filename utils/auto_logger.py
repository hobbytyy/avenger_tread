#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import argparse
from datetime import datetime
import subprocess

class ChangeLogger:
    """与Git预提交钩子联动，自动生成带时间戳的变更记录"""
    
    def __init__(self, log_type="general"):
        self.log_type = log_type
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def get_git_info(self):
        """获取Git相关信息"""
        try:
            # 获取当前分支
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                           stderr=subprocess.DEVNULL).decode().strip()
            
            # 获取最后一次提交哈希
            commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"], 
                                                stderr=subprocess.DEVNULL).decode().strip()[:8]
            
            return {
                "branch": branch,
                "commit": commit_hash
            }
        except subprocess.CalledProcessError:
            return {
                "branch": "unknown",
                "commit": "unknown"
            }
    
    def log_change(self):
        """记录变更"""
        git_info = self.get_git_info()
        
        log_entry = f"[{self.timestamp}] [{self.log_type}] [Branch: {git_info['branch']}] [Commit: {git_info['commit']}]"
        
        # 创建日志目录（如果不存在）
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # 写入日志文件
        log_file = os.path.join(log_dir, "change_log.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
            
        print(f"Change logged: {log_entry}")

def main():
    # 如果没有提供参数，使用默认值
    log_type = "general"
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Auto logger for git pre-commit hook")
    parser.add_argument("--log-type", default="general", help="Type of change to log")
    
    # 检查是否有参数传入
    if len(sys.argv) > 1:
        args = parser.parse_args()
        log_type = args.log_type
    
    logger = ChangeLogger(log_type)
    logger.log_change()

if __name__ == "__main__":
    main()