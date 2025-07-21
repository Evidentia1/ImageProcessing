from backend.utils.gemini_wrapper import gemini_vision_prompt

def get_image_labels(image_path: str) -> list:
    prompt = (
        "Please look at the image and list all clearly visible objects, structures, or notable elements. "
        "Respond only with short keywords separated by commas, without any explanation or extra text."
    )

    labels = gemini_vision_prompt(image_path, prompt)

    # Clean output to list
    if labels:
        return [label.strip() for label in labels.split(",") if label.strip()]
    return []
