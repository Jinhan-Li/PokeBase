# data_pipeline/run_pipeline.py
"""一键执行知识图谱构建管线"""

import sys
import os
import subprocess

def run_pipeline():
    """运行完整的数据管线"""
    print("=== 宝可梦知识图谱构建管线 ===")
    print()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    scripts = [
        ("阶段 0: 缓存原始数据", "phase0_cache_data.py"),
        ("阶段 1: 构建实体节点 (Pokemon, Type, Ability, Move)", "phase1_nodes.py"),
        ("阶段 2: 构建基础拓扑 (HAS_TYPE, HAS_ABILITY, CAN_LEARN)", "phase2_basic_relationships.py"),
        ("阶段 2.5: 构建属性克制 (DAMAGE_TO)", "phase2_5_type.py"),
        ("阶段 3: 构建进化链 (EVOLVES_TO, EVOLVES_FROM)", "phase3_evolution.py"),
    ]
    
    for step_name, script in scripts:
        print("=" * 60)
        print(step_name)
        print("=" * 60)
        
        script_path = os.path.join(current_dir, script)
        if not os.path.exists(script_path):
            print(f"[-] 错误: 找不到脚本 {script_path}")
            sys.exit(1)
            
        try:
            subprocess.run([sys.executable, script_path], check=True, cwd=current_dir)
        except subprocess.CalledProcessError as e:
            print(f"\n[-] 执行 {script} 时发生错误，退出码: {e.returncode}")
            sys.exit(1)
            
        print()
        
    print("🎉 知识图谱所有构建阶段执行完毕！")

if __name__ == "__main__":
    run_pipeline()
