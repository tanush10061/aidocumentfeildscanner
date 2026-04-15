import gradio as gr
import requests

BACKEND_URL = "http://127.0.0.1:8000/extract_invoice/"


def process_invoice(file: str, mode: str):
    """Send the uploaded file to the backend and return parsed JSON or an error."""
    if not file:
        return {"error": "No file provided"}

    try:
        with open(file, "rb") as f:
            files = {"file": f}
            data = {"mode": mode}
            resp = requests.post(BACKEND_URL, files=files, data=data, timeout=60)
        if resp.status_code == 200:
            return resp.json()
        return {
            "error": f"Backend error (status {resp.status_code})",
            "status_code": resp.status_code,
            "response_text": resp.text,
        }
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection failed: {e}", "backend_url": BACKEND_URL}
    except requests.exceptions.Timeout as e:
        return {"error": f"Request timed out: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}", "type": type(e).__name__}


def clear_output():
    return None


def launch_app():
    custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Design tokens */
    :root {
      --app-gradient: linear-gradient(145deg, #e8f2d4 0%, #dde8c7 100%);
      --accent: #6b8e23;          /* olive */
      --accent-dark: #4a5d28;     /* dark olive */
      --text-dark: #2f3e1d;       /* deep green text */
      --brand-orange: #ff7a00;    /* deeper orange for brand accents */
    }

    /* Ensure the green gradient fills the entire UI */
    html, body, .gradio-container, #root, #app, #gradio-app {
      background: var(--app-gradient) !important;
      min-height: 100vh; margin: 0; padding: 0;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
      color: var(--text-dark);
    }

    /* Override Gradio theme tokens to avoid white fills */
    :root, .gradio-container {
      --body-background-fill: transparent !important;
      --background-fill-primary: transparent !important;
      --background-fill-secondary: transparent !important;
      --block-background-fill: transparent !important;
      --panel-background-fill: transparent !important;
      --color-background: transparent !important;
    }

    /* Remove white backgrounds from common containers */
    .block, .panel, .group, .row, .column, .form, .tabs, .tabitem, .container, .gr-panel, .gr-block, .gr-box, .prose {
      background: transparent !important;
    }

    /* Kill common utility backgrounds that may leak in */
    [class*="bg-white"], [class*="bg-gray-50"], [class*="bg-gray-100"], [class*="bg-slate-50"], [class*="bg-neutral-50"] {
      background-color: transparent !important;
    }

    .main-header { text-align: center; padding: 24px 0; color: white;
      background: linear-gradient(135deg, var(--accent) 0%, #556b2f 50%, var(--accent-dark) 100%);
      border-radius: 16px; margin-bottom: 16px; }

    /* Increase heading sizes by 2pt */
    .main-header h1 { font-size: calc(2em + 2pt) !important; }
    .main-header p { font-size: calc(1em + 2pt) !important; }

    /* Results panels: use EXACT same gradient as the page */
    .results-area {
      background: var(--app-gradient) !important;
      border: 1px solid rgba(107, 142, 35, 0.18);
      border-radius: 16px; box-shadow: 0 6px 22px rgba(107,142,35,0.12);
    }
    /* Force inner wrappers to be transparent so gradient shows */
    .results-area * { background: transparent !important; color: var(--text-dark); }

    /* Full-width section header bar (olive, white text) */
    .header-bar {
      background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important;
      color: #fff !important; border-radius: 12px; padding: 12px 16px; font-weight: 700;
      text-align: center; margin: 12px; letter-spacing: .2px;
      box-shadow: 0 4px 12px rgba(76,107,35,.35);
    }

    /* Upload area: EXACT same gradient and higher contrast content */
    .upload-area {
      border: 2px solid var(--accent-dark); border-radius: 12px; padding: 20px;
      background: var(--app-gradient) !important;
    }
    .upload-area * { background: transparent !important; color: var(--text-dark) !important; opacity: 0.95; }
    .upload-area svg { fill: var(--accent-dark) !important; opacity: 0.9; }

    /* Radio controls: larger, clearer, and high-contrast */
    .mode-toggle { padding: 6px 2px; display: flex; gap: 12px; align-items: center; }
    .mode-toggle label { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px;
      border: 2px solid var(--accent-dark); border-radius: 999px; background: #e8f2d4cc;
      color: var(--brand-orange) !important; font-weight: 700; cursor: pointer;
      text-shadow: 0 1px 0 rgba(255,255,255,.35), 0 0 0.5px rgba(0,0,0,.25); }
    .mode-toggle label span { color: var(--brand-orange) !important; }
    .mode-toggle label:hover { background: #f3f9e6; }
    /* Selected state: keep light background; highlight border; text stays brand orange */
    .mode-toggle label:has(input[type="radio"]:checked) {
      background: #eef6db !important;
      color: var(--brand-orange) !important;
      border-color: var(--accent) !important;
      box-shadow: inset 0 0 0 2px rgba(107,142,35,0.15);
      text-shadow: 0 1px 0 rgba(255,255,255,.35), 0 0 0.5px rgba(0,0,0,.25);
    }
    .mode-toggle input[type="radio"] { appearance: auto !important; width: 18px; height: 18px; accent-color: var(--accent); border-radius: 50%; filter: drop-shadow(0 1px 0 rgba(0,0,0,.05)); }

    /* JSON output: transparent background, brand orange text, bold */
    #json-output, #json-output * { background: transparent !important; color: var(--brand-orange) !important; font-weight: 700 !important; }
    #json-output pre { background: transparent !important; font-weight: 700 !important; }

    /* Extract button: more contrast and lift */
    .extract-button { background: linear-gradient(135deg, var(--accent), var(--accent-dark)) !important; color: #fff !important; border-radius: 999px !important; padding: 12px 28px !important; border: none !important; box-shadow: 0 6px 16px rgba(76, 107, 35, 0.35); }
    .extract-button:hover { filter: brightness(1.05); box-shadow: 0 8px 20px rgba(76, 107, 35, 0.45); }
    .extract-button:focus { outline: 2px solid #ffffff55; outline-offset: 2px; }

    /* Fix Gradio footer popups/tooltips/dialogs (API, Built with Gradio, Settings) */
    .gradio-footer-popup, .gradio-tooltip, .gradio-api-popup, .gradio-builtwith-popup, .gradio-settings-popup, .gradio-footer-modal, .gradio-footer-dialog {
      background: #f6f9f1 !important;
      color: #2f3e1d !important;
      opacity: 1 !important;
      box-shadow: 0 2px 24px rgba(60,80,40,0.12) !important;
      border-radius: 12px !important;
      font-weight: 500 !important;
    }
    .gradio-footer-popup *, .gradio-tooltip *, .gradio-api-popup *, .gradio-builtwith-popup *, .gradio-settings-popup *, .gradio-footer-modal *, .gradio-footer-dialog * {
      color: #2f3e1d !important;
      background: transparent !important;
      text-shadow: none !important;
    }
    """
    theme = gr.themes.Base(primary_hue="green", secondary_hue="green", neutral_hue="stone").set(
        body_background_fill="transparent",
        block_background_fill="transparent",
        panel_background_fill="transparent",
        background_fill_primary="transparent",
        background_fill_secondary="transparent",
    )

    with gr.Blocks(css=custom_css, title="Invoice OCR", theme=theme) as demo:
        gr.HTML(
            """
            <div class="main-header">
                <h1 class="gradient-title" style="margin:0;font-weight:500;color:#ff7a00">Invoice OCR</h1>
                <p style="margin:8px 0 0 0;opacity:.95;color:#ffffff">AI-powered document data extraction</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                with gr.Group(elem_classes=["results-area"]):
                    gr.HTML("""<div class='header-bar'>Upload Your Invoice</div>""")
                    with gr.Group():
                        file_input = gr.File(
                            label="",
                            file_count="single",
                            type="filepath",
                            file_types=[".pdf", ".png", ".jpg", ".jpeg"],
                            elem_classes=["upload-area"],
                            show_label=False,
                        )
                        with gr.Group(elem_classes=["mode-toggle"]):
                            mode = gr.Radio(
                                choices=[("AI (High Accuracy)", "paid"), ("OCR (Fast & Free)", "open_source")],
                                value="paid",
                                label="Processing Mode",
                                container=False,
                            )
                        submit = gr.Button("Extract Data", variant="primary", elem_classes=["extract-button"])

            with gr.Column(scale=1):
                with gr.Group(elem_classes=["results-area"]):
                    gr.HTML("""<div class='header-bar'>Extracted Invoice Data</div>""")
                    output = gr.JSON(label="", show_label=False, height=300, elem_id="json-output")

        def process_with_status(file, mode):
            if file is None:
                return {"error": "No file provided"}
            return process_invoice(file, mode)

        submit.click(fn=process_with_status, inputs=[file_input, mode], outputs=[output])
        file_input.change(fn=clear_output, inputs=[], outputs=output)
        mode.change(fn=clear_output, inputs=[], outputs=output)

        demo.launch()


if __name__ == "__main__":
    launch_app()