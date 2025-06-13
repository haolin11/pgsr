import open3d as o3d
import argparse
import sys
import signal
import time

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='3D点云查看器')
    parser.add_argument('--input', '-i', type=str, required=True, help='输入PLY文件路径')
    args = parser.parse_args()
    
    try:
        # 加载PLY文件
        print(f"正在加载文件: {args.input}")
        point_cloud = o3d.io.read_point_cloud(args.input)
        
        # 可视化点云
        print("按Ctrl+C退出程序")
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        vis.add_geometry(point_cloud)
        
        while True:
            vis.poll_events()
            vis.update_renderer()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print('\n程序已退出')
        vis.destroy_window()
        sys.exit(0)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
