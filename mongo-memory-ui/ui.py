import gradio as gr
from service import list_project_ids, get_last_tags, insert_project_context

def get_tags_for_project(project_id):
    if project_id:
        return get_last_tags(project_id)
    return []

def submit_context(project_id, tags, context_type, context_content):
    result = insert_project_context(project_id, tags, context_type, context_content)
    return f"Contexto inserido para o projeto {project_id}. ID: {result.inserted_id}"

def launch_ui():
    with gr.Blocks() as demo:
        project_id = gr.Dropdown(label="Project ID", allow_custom_value=True, interactive=True)
        tags = gr.Textbox(label="Tags", interactive=True)
        context_type = gr.Textbox(label="Context Type", interactive=True)
        context_content = gr.Textbox(label="Context Content (Markdown)", lines=5, interactive=True)
        output = gr.Textbox(label="Resultado", value="")

        def update_project_id_choices():
            return gr.Dropdown(choices=list_project_ids())

        demo.load(fn=update_project_id_choices, inputs=None, outputs=project_id)

        def update_tags(selected_id):
            return ", ".join(get_tags_for_project(selected_id))

        project_id.change(fn=update_tags, inputs=project_id, outputs=tags)

        def on_submit(selected_id, tags_val, type_val, content_val):
            if not selected_id or not selected_id.strip():
                return "Erro: Project ID é obrigatório.", None, "", "", ""
            
            pid = selected_id.strip()
            tags_list = [t.strip() for t in tags_val.split(",") if t.strip()]
            msg = submit_context(pid, tags_list, type_val, content_val)
            # Retorna mensagem e campos limpos (incluindo resetar o resultado)
            return msg, None, "", "", ""

        def clear_fields():
            return "", None, "", "", ""

        submit_btn = gr.Button("Inserir Contexto")
        clear_btn = gr.Button("Limpar Campos")
        
        submit_btn.click(
            fn=on_submit,
            inputs=[project_id, tags, context_type, context_content],
            outputs=[output, project_id, tags, context_type, context_content]
        )
        
        clear_btn.click(
            fn=clear_fields,
            inputs=[],
            outputs=[output, project_id, tags, context_type, context_content]
        )

    demo.launch(server_name="0.0.0.0")
