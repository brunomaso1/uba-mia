"""Mock implementation of a visual agent for testing purposes."""

import json
from typing import Any
from PIL import Image
from loguru import logger


class VisualAgentMock:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def invoke(self, image: Image) -> dict[str, Any]:
        logger.info("VisualAgentMock invoked")
        response_text = """
        {
        "components": [
            "Header title for the contact section",
            "Form container enclosing all input fields",
            "Label and text input for full name",
            "Label and text input for email address",
            "Label and select dropdown for subject with default option",
            "Label and textarea for message",
            "Submit button for sending the form"
        ],
        "layout": "Vertical single-column layout using block-level elements stacked sequentially, likely implemented with CSS flexbox column direction or simple margin-based spacing for form fields; the form is centered within a card-like container with padding and borders for isolation",
        "style": "Clean and minimalistic with rounded corners on form elements, subtle borders on inputs, ample vertical spacing between fields for readability, and a shadowed or elevated card appearance for the overall form container",
        "color_scheme": "Predominantly white background with neutral grays for borders and labels, accented by blue for the primary action button to draw attention",
        "typography": "Sans-serif font family for labels and inputs, bold weight for the section header, standard size for form labels (around 14-16px), and placeholder text in lighter gray for guidance",
        "interactive_elements": [
            "Text input field for entering full name",
            "Text input field for entering email address",
            "Select dropdown for choosing subject with predefined options",
            "Textarea for composing the message",
            "Submit button to process and send the form data"
        ],
        "design_patterns": [
            "Standard contact form pattern with sequential input fields",
            "Card-based container for form isolation and focus",
            "Label-input pairing for accessibility and clarity",
            "Primary action button at the bottom for conversion flow",
            "Dropdown for categorized inquiries to streamline user input"
        ],
        "analysis_text": "This UI design represents a classic contact form component, structured as a self-contained card with a prominent header title 'Get In Touch' followed by a vertical stack of form controls. In HTML terms, it would use a <form> element as the root container, with <h2> or <h3> for the title, and child elements including <label> paired with <input type='text'> for name and email, <label> with <select> for subject (containing <option> elements like 'General Inquiry'), <label> with <textarea> for message, and a <button type='submit'> styled as primary. CSS implementation likely employs flexbox (display: flex; flex-direction: column; gap: 1rem;) for spacing between fields, with the form wrapped in a div classed as 'card' using border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 2rem; for elevation. Inputs share styles like border: 1px solid #ddd; padding: 0.75rem; border-radius: 4px; background: white;, with focus states adding outline or border color change to blue (#007bff). The submit button uses background: #007bff; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 4px; for prominence. Typography via font-family: 'Arial', sans-serif; with header font-size: 1.5rem; font-weight: bold;, labels at font-size: 0.875rem; color: #333;. This pattern is common in responsive web forms, adaptable via media queries for mobile (e.g., full-width inputs), and supports accessibility with aria-labels and required attributes for validation. Similar examples can be found in Bootstrap's form components or Material Design's outlined text fields, ideal for lead generation pages in marketing sites.",
        "image_metadata": {
            "dimensions": {
            "width": 459,
            "height": 571,
            "aspect_ratio": 0.8038528896672504
            },
            "dominant_colors": [],
            "layout_hints": {
            "complexity": "unknown"
            },
            "file_size": 786300,
            "format": "JPEG"
        },
        "model_used": "mistralai/mistral-small-3.1-24b-instruct:free",
        "analysis_timestamp": null
        }
        """
        response: dict[str, Any] = {}
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError("Failed to parse response JSON") from e
        return response
