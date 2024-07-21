from typing import TYPE_CHECKING, Any, Dict, Optional
import streamlit as st
from langchain_core.callbacks import BaseCallbackHandler
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
import pandas as pd
from io import StringIO

class MyCustomHandler(BaseCallbackHandler):    
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Entrando em uma processo"""
        st.session_state.messages.append({"role": "assistant", "content": inputs['input']})
        st.chat_message("assistant").write(inputs['input'])
   
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Finalizando um processo"""
        st.session_state.messages.append({"role": self.agent_name, "content": outputs['output']})
        st.chat_message(self.agent_name).write(outputs['output'])

def create_pdf(df1, df2, df3, preparo_str):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Determinar larguras das colunas baseadas no conteúdo e nos títulos
    def calculate_column_widths(dataframe):
        col_widths = []
        for col in dataframe.columns:
            max_width = c.stringWidth(col, "Helvetica-Bold", 10) + 30
            for row in dataframe[col]:
                max_width = max(max_width, c.stringWidth(str(row), "Helvetica", 9) + 30)
            col_widths.append(max_width)
        return col_widths

    # Função auxiliar para desenhar uma tabela
    def draw_table(c, dataframe, x, y, title):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, title)
        y -= 20

        col_widths = calculate_column_widths(dataframe)

        # Verificar se a largura total excede a largura da página e ajustar proporcionalmente
        total_width = sum(col_widths)
        if total_width > (width - 60):
            pages_needed = (total_width + width - 60 - 1) // (width - 60)
        else:
            pages_needed = 1
        
        cols_per_page = len(dataframe.columns) // pages_needed
        if len(dataframe.columns) % pages_needed != 0:
            cols_per_page += 1

        for page in range(pages_needed):
            x_offset = x
            start_col = page * cols_per_page
            end_col = min((page + 1) * cols_per_page, len(dataframe.columns))
            
            # Escrever cabeçalhos das colunas em negrito
            for col_num in range(start_col, end_col):
                col_name = dataframe.columns[col_num]
                c.drawString(x_offset + 5, y - 15, col_name)
                c.rect(x_offset, y - 20, col_widths[col_num], 20)
                x_offset += col_widths[col_num]

            y -= 20

            # Escrever dados da tabela com fonte normal
            c.setFont("Helvetica", 10)
            for i, row in dataframe.iterrows():
                x_offset = x
                for col_num in range(start_col, end_col):
                    value = row[col_num]
                    c.drawString(x_offset + 5, y - 15, str(value))
                    c.rect(x_offset, y - 20, col_widths[col_num], 20)
                    x_offset += col_widths[col_num]
                y -= 20

            if page < pages_needed - 1:
                c.showPage()
                c.setFont("Helvetica-Bold", 15)
                c.drawCentredString(width / 2, height - 40, "Ficha Técnica")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x, height - 60, title)
                y = height - 80

        return y - 20

    def draw_string(c, text, x, y, width, height, title):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, title)
        y -= 20
        c.setFont("Helvetica", 10)

        lines = []
        paragraphs = text.split('\n')
        for paragraph in paragraphs:
            if paragraph.strip() == '':
                continue
            if paragraph[0].isdigit() and paragraph[1] == '.':
                if lines:
                    lines.append('')
                lines.append(paragraph)
            else:
                if lines and lines[-1] != '':
                    lines[-1] += ' ' + paragraph
                else:
                    lines.append(paragraph)

        for line in lines:
            if y < 40:
                c.showPage()
                c.setFont("Helvetica-Bold", 15)
                c.drawCentredString(width / 2, height - 40, "Ficha Técnica")
                c.setFont("Helvetica-Bold", 12)
                c.drawString(x, height - 60, title)
                y = height - 80
                c.setFont("Helvetica", 10)
            c.drawString(x, y, line)
            y -= 15

        return y

    # Iniciar o documento e adicionar as tabelas
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(width / 2, height - 40, "Ficha Técnica")

    y = height - 60

    y = draw_table(c, df1, 30, y, "Tabela 1: Receita")
    y = draw_table(c, df2, 30, y, "Tabela 2: Ingredientes")
    y = draw_table(c, df3, 30, y, "Tabela 3: Valor Nutricional")
    y = draw_string(c, preparo_str, 30, y, width, height, "Modo de Preparo")

    c.save()
    buffer.seek(0)
    return buffer

def save_excel(df1, df2, df3):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df1.to_excel(writer, sheet_name='Receita', index=False)
        df2.to_excel(writer, sheet_name='Ingredientes', index=False)
        df3.to_excel(writer, sheet_name='Valor Nutricional', index=False)
    return output

def save_csv(df1, df2,df3):
    output = BytesIO()
    output.write(df1.to_csv(index=False, encoding='latin-1').encode('latin-1'))
    output.write(b"\n")  # Adiciona uma linha em branco entre os dataframes
    output.write(df2.to_csv(index=False, encoding='latin-1').encode('latin-1'))
    output.write(b"\n")  # Adiciona uma linha em branco entre os dataframes
    output.write(df3.to_csv(index=False, encoding='latin-1').encode('latin-1'))
    output.seek(0)
    return output