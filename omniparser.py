from PIL import Image

from util.utils import check_ocr_box, get_yolo_model, get_caption_model_processor, get_som_labeled_img

class OmniParser:
    def __init__(self) -> None:
        self.__yolo_model = get_yolo_model(model_path='weights/icon_detect/model.pt')
        self.__caption_model_processor = get_caption_model_processor(model_name="florence2", model_name_or_path="weights/icon_caption_florence")
        
    def parse_image(self, image_path: str) -> tuple[dict, str]:
        image_input = Image.open(image_path)
        
        box_overlay_ratio = image_input.size[0] / 3200
        draw_bbox_config = {
            'text_scale': 0.8 * box_overlay_ratio,
            'text_thickness': max(int(2 * box_overlay_ratio), 1),
            'text_padding': max(int(3 * box_overlay_ratio), 1),
            'thickness': max(int(3 * box_overlay_ratio), 1),
        }
        
        ocr_bbox_rslt, is_goal_filtered = check_ocr_box(
            image_input, 
            display_img=False, 
            output_bb_format='xyxy', 
            goal_filtering=None, 
            easyocr_args={'paragraph': False, 'text_threshold': 0.9}, 
            use_paddleocr=False
        )
        
        text, ocr_bbox = ocr_bbox_rslt
        
        dino_labled_img, label_coordinates, parsed_content_list = get_som_labeled_img(
            image_input,
            self.__yolo_model,
            BOX_TRESHOLD=0.05,
            output_coord_in_ratio=True,
            ocr_bbox=ocr_bbox,
            draw_bbox_config=draw_bbox_config,
            caption_model_processor=self.__caption_model_processor,
            ocr_text=text,
            iou_threshold=0.1,
            imgsz=640,
        )

        numbered_parsed_content_list = {i+1 : content for i, content in enumerate(parsed_content_list)}
        
        return numbered_parsed_content_list, dino_labled_img