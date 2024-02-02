from analyse.pipeline import process_pipeline
import kg.attach as attach
from kg.dump import dump, visualize
import interpret.disambi as disambi
import interpret.llm as llm
import os
import logging
import paddle
from PIL import Image

def main(img_path, output_path, debug=True, erode=True, tmp_dir = None):
    texts, devices, lines = process_pipeline(img_path, debug, erode=erode, tmp_dir = tmp_dir)
    image = Image.open(img_path)
    size0 = image.size[0]
    size1 = image.size[1]
    image.close()
    adjust_ratio = max(1.0, (size0**2 + size1**2)**0.5/800)
    ports = attach.attach_line_ends(devices, lines, ADJUST_RATIO=adjust_ratio)
    attach.attach_all(texts, devices, lines, ports, ADJUST_RATIO=adjust_ratio)
    attach.remove_duplicate_lines(devices, lines, ports)
    json_path = os.path.join(output_path, os.path.splitext(os.path.basename(img_path))[0] + ".json")
    dump(devices, lines, ports, json_path)
    disambi.optimize_json(devices, lines, ports)
    json_path = os.path.join(output_path, os.path.splitext(os.path.basename(img_path))[0] + "_optimized.json")
    dump(devices, lines, ports, json_path)
    # The following code helps you to visualize the result
    # visualize(devices, lines, ports, os.path.join(output_path, "viz_" + os.path.splitext(os.path.basename(img_path))[0] + "_optimized.jpg"), size0, size1)
    print(llm.convert_json(json_path), file=open(os.path.join(output_path, os.path.splitext(os.path.basename(img_path))[0] + "_optimized.txt"), "w"))



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='LEND script discription')

    parser.add_argument('--img_path', type=str, required=True, help='the path to the image file to be processed.')
    parser.add_argument('--output_dir', type=str, required=True, help='the path to save NDJ and LLM prompt.')
    parser.add_argument('--erode', type=bool, default=True, help='Erode the diagram for better filter of noises. Default: True. set to False if line is thin.')
    parser.add_argument('--tmp_dir', type=str, default=None, help='the directory to place temporary files. Default: None')
    parser.add_argument('--debug', type=bool, default=False, help='set to True to enable debug mode. Default: False')

    args = parser.parse_args()

    if (not args.debug):
        paddle.disable_static()
        logging.disable(logging.DEBUG)
        logging.disable(logging.WARNING)

    main(args.img_path, args.output_dir, debug=args.debug, erode=args.erode, tmp_dir=args.tmp_dir)