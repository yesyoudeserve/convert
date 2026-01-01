"""
API de Conversão HTML para PDF
Desenvolvido para n8n + Easypanel
"""

from flask import Flask, request, send_file, jsonify
from weasyprint import HTML
from io import BytesIO
import logging

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def home():
    """Endpoint de health check"""
    return jsonify({
        'status': 'online',
        'service': 'HTML to PDF Converter',
        'version': '1.0.0',
        'endpoints': {
            '/convert': 'POST - Converte HTML para PDF',
            '/health': 'GET - Health check'
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check para monitoramento"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/convert', methods=['POST'])
def convert_html_to_pdf():
    """
    Converte HTML para PDF
    
    Aceita:
    - Content-Type: text/html (HTML direto no body)
    - Content-Type: application/json (JSON com campo 'html')
    - Content-Type: multipart/form-data (arquivo HTML)
    
    Retorna: PDF file
    """
    try:
        html_content = None
        
        # Opção 1: HTML direto no body (text/html)
        if request.content_type and 'text/html' in request.content_type:
            html_content = request.data.decode('utf-8')
            logger.info("Recebido HTML via text/html")
        
        # Opção 2: JSON com campo 'html'
        elif request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            html_content = data.get('html')
            logger.info("Recebido HTML via JSON")
        
        # Opção 3: Arquivo enviado via form-data
        elif 'file' in request.files:
            file = request.files['file']
            html_content = file.read().decode('utf-8')
            logger.info("Recebido HTML via arquivo")
        
        # Opção 4: HTML no campo 'html' do form-data
        elif 'html' in request.form:
            html_content = request.form['html']
            logger.info("Recebido HTML via form-data")
        
        if not html_content:
            return jsonify({
                'error': 'Nenhum HTML fornecido',
                'aceita': [
                    'Content-Type: text/html (HTML no body)',
                    'Content-Type: application/json ({"html": "..."})',
                    'multipart/form-data (file ou html)'
                ]
            }), 400
        
        # Converter HTML para PDF
        logger.info(f"Convertendo HTML ({len(html_content)} chars) para PDF")
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Criar buffer e retornar PDF
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        logger.info(f"PDF gerado com sucesso ({len(pdf_bytes)} bytes)")
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='documento.pdf'
        )
    
    except Exception as e:
        logger.error(f"Erro ao converter PDF: {str(e)}")
        return jsonify({
            'error': 'Erro ao converter PDF',
            'details': str(e)
        }), 500

@app.route('/convert-with-params', methods=['POST'])
def convert_with_params():
    """
    Converte HTML para PDF com parâmetros adicionais
    
    JSON esperado:
    {
        "html": "<html>...</html>",
        "filename": "documento.pdf" (opcional),
        "page_size": "A4" (opcional),
        "orientation": "portrait" ou "landscape" (opcional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({'error': 'Campo "html" é obrigatório'}), 400
        
        html_content = data['html']
        filename = data.get('filename', 'documento.pdf')
        page_size = data.get('page_size', 'A4')
        orientation = data.get('orientation', 'portrait')
        
        # Adicionar CSS de página se necessário
        if page_size or orientation:
            css_rules = []
            if page_size:
                css_rules.append(f'size: {page_size}')
            if orientation:
                css_rules.append(f'{orientation}')
            
            page_css = f'<style>@page {{ {"; ".join(css_rules)}; margin: 0; }}</style>'
            
            # Inserir CSS no HTML
            if '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head>{page_css}')
            else:
                html_content = f'<html><head>{page_css}</head><body>{html_content}</body></html>'
        
        # Converter
        logger.info(f"Convertendo com params: size={page_size}, orientation={orientation}")
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Porta 8080 (padrão Easypanel)
    app.run(host='0.0.0.0', port=8080, debug=False)
