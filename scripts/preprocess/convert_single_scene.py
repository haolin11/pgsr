import os
import logging
from argparse import ArgumentParser
import shutil

def init_colmap(args):
    colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
    magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"
    use_gpu = 1 if not args.no_gpu else 0
    
    scene_path = args.data_path
    os.makedirs(os.path.join(scene_path, "sparse"), exist_ok=True)

    # 删除已存在的文件
    if os.path.exists(os.path.join(scene_path, "database.db")):
        os.remove(os.path.join(scene_path, "database.db"))
    if os.path.exists(os.path.join(scene_path, "sparse")):
        shutil.rmtree(os.path.join(scene_path, "sparse"))
    os.makedirs(os.path.join(scene_path, "sparse"), exist_ok=True)

    ## Feature extraction
    feat_extracton_cmd = colmap_command + " feature_extractor "\
        "--database_path " + os.path.join(scene_path, "database.db") + " "\
        "--image_path " + os.path.join(scene_path, "input") + " "\
        "--ImageReader.single_camera 1 "\
        "--ImageReader.camera_model " + args.camera + " "\
        "--SiftExtraction.use_gpu " + str(use_gpu)
    exit_code = os.system(feat_extracton_cmd)
    if exit_code != 0:
        logging.error(f"Feature extraction failed with code {exit_code}. Exiting.")
        exit(exit_code)

    ## Feature matching
    feat_matching_cmd = colmap_command + " exhaustive_matcher "\
        "--database_path " + os.path.join(scene_path, "database.db") + " "\
        "--SiftMatching.use_gpu " + str(use_gpu)
    exit_code = os.system(feat_matching_cmd)
    if exit_code != 0:
        logging.error(f"Feature matching failed with code {exit_code}. Exiting.")
        exit(exit_code)

    ### Bundle adjustment
    # The default Mapper tolerance is unnecessarily large,
    # decreasing it speeds up bundle adjustment steps.
    mapper_cmd = (colmap_command + " mapper "\
        "--database_path " + os.path.join(scene_path, "database.db") + " "\
        "--image_path " + os.path.join(scene_path, "input") + " "\
        "--output_path " + os.path.join(scene_path, "sparse") + " "\
        "--Mapper.ba_global_function_tolerance=0.000001")
    exit_code = os.system(mapper_cmd) 
    if exit_code != 0:
        logging.error(f"Mapper failed with code {exit_code}. Exiting.")
        exit(exit_code)

    # 检查sparse/0目录是否存在
    sparse_0_dir = os.path.join(scene_path, "sparse", "0")
    if os.path.exists(sparse_0_dir):
        files = os.listdir(sparse_0_dir)
        # Copy each file from the source directory to the destination directory
        for file in files:
            destination_file = os.path.join(scene_path, "sparse", file)
            source_file = os.path.join(sparse_0_dir, file)
            shutil.move(source_file, destination_file)
        # 删除空的sparse/0目录
        os.rmdir(sparse_0_dir)

    ### Image undistortion
    ## We need to undistort our images into ideal pinhole intrinsics.
    img_undist_cmd = (colmap_command + " image_undistorter "\
        "--image_path " + os.path.join(scene_path, "input") + " "\
        "--input_path " + os.path.join(scene_path, "sparse") + " "\
        "--output_path " + scene_path + " "\
        "--output_type COLMAP")
    exit_code = os.system(img_undist_cmd)
    if exit_code != 0:
        logging.error(f"Image undistortion failed with code {exit_code}. Exiting.")
        exit(exit_code)

    if(args.resize):
        print("Copying and resizing...")

        # Resize images.
        os.makedirs(os.path.join(scene_path, "images_2"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "images_4"), exist_ok=True)
        os.makedirs(os.path.join(scene_path, "images_8"), exist_ok=True)
        
        # Get the list of files in the source directory
        images_dir = os.path.join(scene_path, "images")
        if os.path.exists(images_dir):
            files = os.listdir(images_dir)
            # Copy each file from the source directory to the destination directory
            for file in files:
                source_file = os.path.join(images_dir, file)

                destination_file = os.path.join(scene_path, "images_2", file)
                shutil.copy2(source_file, destination_file)
                exit_code = os.system(magick_command + " mogrify -resize 50% " + destination_file)
                if exit_code != 0:
                    logging.error(f"50% resize failed with code {exit_code}. Exiting.")
                    exit(exit_code)

                destination_file = os.path.join(scene_path, "images_4", file)
                shutil.copy2(source_file, destination_file)
                exit_code = os.system(magick_command + " mogrify -resize 25% " + destination_file)
                if exit_code != 0:
                    logging.error(f"25% resize failed with code {exit_code}. Exiting.")
                    exit(exit_code)

                destination_file = os.path.join(scene_path, "images_8", file)
                shutil.copy2(source_file, destination_file)
                exit_code = os.system(magick_command + " mogrify -resize 12.5% " + destination_file)
                if exit_code != 0:
                    logging.error(f"12.5% resize failed with code {exit_code}. Exiting.")
                    exit(exit_code)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser = ArgumentParser("Colmap converter for single scene")
    parser.add_argument('--data_path', type=str, required=True, help='Path to scene directory (e.g., data/my_dataset/stone)')
    parser.add_argument("--no_gpu", action='store_true')
    parser.add_argument("--camera", default="OPENCV", type=str)
    parser.add_argument("--colmap_executable", default="", type=str)
    parser.add_argument("--resize", action="store_true")
    parser.add_argument("--magick_executable", default="", type=str)
    args = parser.parse_args()

    init_colmap(args)

    print("Done.") 