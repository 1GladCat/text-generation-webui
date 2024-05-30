from pathlib import Path

import gradio as gr

from modules.html_generator import get_image_cache
from modules.shared import gradio


params = {
    'items_per_page': 50,
    'open': False,
}

cards = []
current_directory = Path('characters')


def generate_css():
    css = """
      .highlighted-border {
        border-color: rgb(249, 115, 22) !important;
      }

      .character-gallery > .gallery {
        margin: 1rem 0;
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        grid-column-gap: 0.4rem;
        grid-row-gap: 1.2rem;
      }

      .character-gallery > .label {
        display: none !important;
      }

      .character-gallery button.gallery-item {
        display: contents;
      }

      .character-container {
        cursor: pointer;
        text-align: center;
        position: relative;
        opacity: 0.85;
      }

      .character-container:hover {
        opacity: 1;
      }

      .character-container .placeholder, .character-container img {
        width: 150px;
        height: 200px;
        background-color: gray;
        object-fit: cover;
        margin: 0 auto;
        border-radius: 1rem;
        border: 3px solid white;
        box-shadow: 3px 3px 6px 0px rgb(0 0 0 / 50%);
      }

      .character-name {
        margin-top: 0.3rem;
        display: block;
        font-size: 1.2rem;
        font-weight: 600;
        overflow-wrap: anywhere;
      }

      .folder {
        display: flex;
        align-items: center;
      }
      .folder svg {
        margin: 0 auto;
        width: 80%;
        height: 80%;
      }
    """
    return css


def generate_html(init_path: str = ""):
    global cards
    cards = []
    # Iterate through files in image folder
    for path in sorted(Path(f'characters/{init_path}').glob("*")):
        container_html = '<div class="character-container">'
        # Bootstrap Icon: https://icons.getbootstrap.com/icons/folder/
        icon_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-folder" viewBox="0 0 16 16">
            <path d="M.54 3.87.5 3a2 2 0 0 1 2-2h3.672a2 2 0 0 1 1.414.586l.828.828A2 2 0 0 0 9.828 3h3.982a2 2 0 0 1 1.992 2.181l-.637 7A2 2 0 0 1 13.174 14H2.826a2 2 0 0 1-1.991-1.819l-.637-7a2 2 0 0 1 .342-1.31zM2.19 4a1 1 0 0 0-.996 1.09l.637 7a1 1 0 0 0 .995.91h10.348a1 1 0 0 0 .995-.91l.637-7A1 1 0 0 0 13.81 4zm4.69-1.707A1 1 0 0 0 6.172 2H2.5a1 1 0 0 0-1 .981l.006.139q.323-.119.684-.12h5.396z"/></svg>"""

        if path.is_dir():
            image_html = f"<div class='placeholder folder'>{icon_svg}</div>"
            for image_path in [Path(f"{path}.{extension}") for extension in ['png', 'jpg', 'jpeg']]:
                if image_path.exists():
                    image_html = f'<img src="file/{get_image_cache(image_path)}">'
                    break

            container_html += f'<div>{image_html}</div><span class="character-name">{path.name}</span>'
            container_html += "</div>"
            cards.insert(0, [container_html, f"folder:{path}"])

        elif path.is_file() and path.suffix in [".json", ".yml", ".yaml"]:
            image_html = "<div class='placeholder'></div>"
            for image_path in [Path(f"{str(path).removesuffix(path.suffix)}.{extension}") for extension in ['png', 'jpg', 'jpeg']]:
                if image_path.exists():
                    image_html = f'<img src="file/{get_image_cache(image_path)}">'
                    break

            container_html += f'{image_html}<span class="character-name">{path.stem}</span>'
            container_html += "</div>"
            cards.append([container_html, f"character:{path}"])

    return cards


def filter_cards(filter_str=''):
    if filter_str == '':
        return cards

    filter_upper = filter_str.upper()
    return [k for k in cards if filter_upper in k[1].upper()]


def select_card(evt: gr.SelectData):
    global current_directory
    card = str(evt.value[1]).split(':')
    path = Path(card[1]).relative_to('characters/')
    if card[0] == 'folder':
        current_directory = path
        generate_html(init_path=path)
        return gr.skip()
    elif card[0] == 'character':
        return str(path).removesuffix(path.suffix)


def prev_folder():
    global current_directory
    if current_directory and current_directory != '.':
        current_directory = current_directory.parent
        generate_html(str(current_directory))


def custom_js():
    path_to_js = Path(__file__).parent.resolve() / 'script.js'
    return open(path_to_js, 'r').read()


def ui():
    with gr.Accordion("Character gallery", open=params["open"], elem_id='gallery-extension'):
        gr.HTML(value="<style>" + generate_css() + "</style>")
        with gr.Row():
            filter_box = gr.Textbox(label='', placeholder='Filter', lines=1, max_lines=1, container=False, elem_id='gallery-filter-box')
            gr.ClearButton(filter_box, value='Clear', elem_classes='refresh-button')
            update = gr.Button("Refresh", elem_classes='refresh-button')
            back = gr.Button("Back", elem_classes='refresh-button')

        gallery = gr.Dataset(
            components=[gr.HTML(visible=False)],
            label="",
            samples=generate_html(),
            elem_classes=["character-gallery"],
            samples_per_page=params["items_per_page"]
        )

    filter_box.change(lambda: None, None, None, js=f'() => {{{custom_js()}; gotoFirstPage()}}').success(
        filter_cards, filter_box, gallery).then(
        lambda x: gr.update(elem_classes='highlighted-border' if x != '' else ''), filter_box, filter_box, show_progress=False)

    update.click(lambda: generate_html(str(current_directory)), None, None).success(
        filter_cards, filter_box, gallery)

    back.click(prev_folder, None, None).success(
        filter_cards, filter_box, gallery)

    gallery.select(select_card, None, gradio['character_menu']).success(
        filter_cards, filter_box, gallery)
