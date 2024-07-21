import streamlit as st
from openai import OpenAI
from crewai import Agent, Task, Crew, Process
from langchain_core.callbacks import BaseCallbackHandler
from typing import TYPE_CHECKING, Any, Dict, Optional
from langchain_openai import ChatOpenAI
from agentes import create_pdf, MyCustomHandler
import pandas as pd
import ast


df_1 = pd.DataFrame()
df_2 = pd.DataFrame()
df_3 = pd.DataFrame()
modo_preparo_str = ''

def format_dataframe(df):
    return df.map(lambda x: f'{x:.2f}' if isinstance(x, (int, float)) else x)
        
if 'df1' not in st.session_state:
    st.session_state.df1 = df_1
if 'df2' not in st.session_state:            
    st.session_state.df2 = df_2
if 'df3' not in st.session_state:
    st.session_state.df3 = df_3
if 'preparo_str' not in st.session_state:
    st.session_state.preparo_str = modo_preparo_str

def initialize_data(df_1, df_2, df_3, modo_preparo_str):
    global df1, df2, df3, preparo_str
    st.session_state.df1 = pd.DataFrame(format_dataframe(df_1))
    st.session_state.df2 = pd.DataFrame(format_dataframe(df_2))
    st.session_state.df3 = pd.DataFrame(format_dataframe(df_3))
    st.session_state.preparo_str = modo_preparo_str

tab1, tab2 = st.tabs(['Geração de Fichas', 'Editar Receitas'])
with tab1:
    api_key=st.secrets["OPENAI_API_KEY"]
    openai_llm = ChatOpenAI(model_name = 'gpt-4-1106-preview', api_key = api_key)

    agente_cria_fichas = Agent(
            role='Criador de Fichas Tecnicas',
            goal='''
            Receber informações sobre uma receita, informada pelo usuário, e gerar três tabelas distintas: a primeira contendo o 'nome da receita', 'tipo', 'rendimento', 'custo da receita' (soma dos valores finais na receita de cada um dos ingrediente), 
            'preço de venda' (preço recomendado para vender a receita), 'lucro bruto' (diferença entre custo da receita e preço de venda, e deve sempre ser positivo) e 'valor unitário' (custo da receita dividido pelo rendimento da receita). Os valores dessa tabela só 
            devem ser preenchidos após a segunda tabela estar concluida, com todos os seus devidos cálculos, mas ainda deve ser exibida primeiro ao usuário.; e a 
            segunda detalhando os ingredientes necessários para a receita, com as colunas 'quantidades (em Kg)', 'valor unitário (do Kg)', e 'valor final' (valor unitário dividido pela quantidade). 
            Lembre-se de que o "Custo da Receita" na tabela 1 é a soma de todos os resultados de "valor final' da tabela 2. Então calcule o 'valor final' com cuidado e, depois disso, some-os e passe esse resultado para 'custo da receita' na tabela 1.
            Não coloque nenhum outro valor em 'custo da receita' na tabela 1 antes de gerar a soma dos valores finais na tabela 2 e confirme se o valor total da soma dos 'valores finais' da tabela 2 é o mesmo do 'custo da receita' na tabela 1.
            A terceira e última tabela será o valor nutricional da receita.
            As tabelas já serão uma ficha técnica final pronta com TODOS os valores preenchidos por você, sem que o usuário precise fazer uma pesquisa de mercado sobre os preços nem fazer cálculos, tudo será feito por você.
            Sempre preencha as tabelas com valores reais coletados em pesquisa ou baseados em cálculos, e não variáveis para o usuário substituir. 
            Atente-se aos cálculos para não cometer nenhum erro e preencha as tabelas baseadas nesses cálculos corretos, mas não precisa mostrar os cálculos ao usuário. 
            Após tudo finalizado, faça uma rechecagem de todos os cálculos feitos, especialmente o somatório dos valores finais de ingredientes e, consequentemente, o valor de "custo de receita" 
            e corrija-os. Garanta que todos os cálculos estão corretos. Após essa rechecagem, faça OUTRA rechecagem. Porém, não precisa falar ao usuário sobre as rechecagens nem os cálculos, apenas mostre a descrição e as tabelas, nessa ordem. 
            As tabelas devem estar bem formatadas, com tudo em português e prontas para serem revisadas e utilizadas por outros agentes ou usuários.
            ''',
            backstory='''
            Você foi desenvolvido para auxiliar chefs e gerentes de restaurantes a organizar e gerenciar suas receitas de maneira eficiente. Além de uma ótimo background em análises estatísticas e cálculos matemáticos, que permitem que 
            você seja sempre preciso nos seus cálculos, você também conhece bastante sobre o mundo culinário. Com uma vasta base de dados de 
            receitas, ingredientes e preços de varejo, você consegue rapidamente transformar informações básicas em tabelas técnicas que facilitam o planejamento e a execução de pratos. 
            Sua precisão e atenção aos detalhes são suas principais qualidades, garantindo que cada receita esteja devidamente documentada.
            ''',
            llm = openai_llm,
            # callbacks=[MyCustomHandler("Criador")]
        )

    agente_organiza_tabelas = Agent(
            role='Gerador de Dataframes',
            goal = '''
            Receber as três tabelas geradas pelo primeiro agente, e então transformá-las em três dataframes distintos: 
            um contendo a parte geral da ficha técnica (nome da receita, tipo e preço), outro com os ingredientes e outro com o valor nutricional. Estes dataframes devem estar prontos para 
            análise ou manipulação posterior.
            ''',
            backstory = '''
            Com um histórico em análise de dados e uma paixão pela culinária, você foi criado para unir essas duas áreas de forma eficiente. Sua capacidade de 
            entender e manipular dados permite que restaurantes e cozinheiros melhorem suas operações e receitas. Você garante que todas as informações são precisas 
            e prontas para serem usadas em análises mais complexas ou em sistemas de gestão de receitas.
            ''',
            llm = openai_llm,
            # callbacks=[MyCustomHandler("Organizador")]
        )

    st.title("Assistente de Ficha Técnica 📊")
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Que receita você quer fazer hoje?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Qual ficha técnica você quer fazer hoje?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        tarefa_criacao_ficha = Task(
            description = f'''
            Coletar informações sobre {prompt} e gerar sua ficha técnica, buscando os valores correspondentes de quantidades e preços
            sem a necessidade do usuário informar nenhum valor extra. Porém, caso ele informe, você adiciona essa informação que ele passou.        
            ''',
            expected_output = ''' 
            Em português, uma breve descrição da receita, seguida das três tabelas geradas pelos agentes e o modo de preparo, com os passos do modo de preparo enumerados de 1 até N, sendo N o número do passo final, sem nenhuma explicação de cálculo, apenas a descrição, as três tabelas e o modo de preparo.
            As tabelas devem estar bem formatadas, com os cálculos corretos, com tudo em português e prontas para serem revisadas e utilizadas por outros agentes ou usuários.
            ''',
            agent = agente_cria_fichas
        )          

        equipe1 = Crew(
            agents = [agente_cria_fichas],
            tasks = [tarefa_criacao_ficha],
            manager_llm=openai_llm,
            verbose= True
        )

        # Iniciar
        fim = equipe1.kickoff()
        st.session_state.messages.append({"role": "assistant", "content": fim})
        st.chat_message("assistant").write(fim)

        tarefa_organiza_tabelas = Task(
            description = f'''
            Com base nas tabelas criadas em {fim}, crie um dataframe específico para cada uma e um texto corrido do modo de preparo que começará com "Modo de Preparo:" e terminará com "Fim.".
            ''',
            expected_output = 'três dicionários que serão, depois, convertidos em dataframes organizados (Dataframe 1, Dataframe 2 e Dataframe 3), em português, e prontos para serem usados posteriormente, e o modo de preparo com o texto inteiro em português',
            agent = agente_organiza_tabelas
        )

        equipe2 = Crew(
            agents = [agente_organiza_tabelas],
            tasks = [tarefa_organiza_tabelas],
            manager_llm=openai_llm,
            verbose = True
        )

        resultados = equipe2.kickoff()
        print(resultados)
        dataframe_1_start = resultados.find("{")
        dataframe_1_end = resultados.find("}") + 1
        dataframe_1_str = resultados[dataframe_1_start:dataframe_1_end]
        dataframe_1_dict = ast.literal_eval(dataframe_1_str)

        dataframe_2_start = resultados.find("{", dataframe_1_end)
        dataframe_2_end = resultados.find("}", dataframe_2_start) + 1
        dataframe_2_str = resultados[dataframe_2_start:dataframe_2_end]
        dataframe_2_dict = ast.literal_eval(dataframe_2_str)

        dataframe_3_start = resultados.find("{", dataframe_2_end)
        dataframe_3_end = resultados.find("}", dataframe_3_start) + 1
        dataframe_3_str = resultados[dataframe_3_start:dataframe_3_end]
        dataframe_3_dict = ast.literal_eval(dataframe_3_str)

        modo_preparo_start = resultados.find("Modo de Preparo:")
        modo_preparo_end = resultados.find("Fim.", modo_preparo_start) + len("Fim.") -4
        modo_preparo_str = resultados[modo_preparo_start:modo_preparo_end]
        start_idx = modo_preparo_str.find("1.")
        modo_preparo_str = modo_preparo_str[start_idx:]

        df_1_novo = pd.DataFrame(dataframe_1_dict)
        df_2_novo = pd.DataFrame(dataframe_2_dict)
        df_3_novo = pd.DataFrame(dataframe_3_dict)

        df_1 = df_1_novo
        df_2 = df_2_novo
        df_3 = df_3_novo

        nome_receita = df_1['Nome da Receita'][0]
        st.session_state.nome_receita = nome_receita        
        initialize_data(df_1, df_2, df_3, modo_preparo_str)

        st.markdown('Suas tabelas já estão prontas para serem analisadas e editadas na seção "Editar Receitas"')

with tab2:  
    def create_inputs(df, row=None):
        inputs = {}
        for col in df.columns:
            if row is not None:
                inputs[col] = st.text_input(col, value=row[col])
            else:
                inputs[col] = st.text_input(col)
        return inputs
    
    # Se existirem, inicializar os dados
    st.title("Editar sua receita 📊")
    # Exibir o Dataframe 1
    st.subheader("Tabela de Receita")
    st.table(st.session_state.df1)   
    # Selecionando a linha para editar ou adicionar uma nova linha
    options1 = [f'Linha {i}' for i in range(len(st.session_state.df1))]
    selected_option1 = st.selectbox('Edite os detalhes principais de sua receita', options1, key='df1_select')
    
    if selected_option1:
        row_index1 = int(selected_option1.split(' ')[1])
        row_data1 = st.session_state.df1.iloc[row_index1]
        inputs1 = create_inputs(st.session_state.df1, row=row_data1)
        col1, col2 = st.columns(2)
        with col1:
            btn_update1 = st.button('Atualizar Receita')
            
        if btn_update1:
            for col in st.session_state.df1.columns:
                st.session_state.df1.at[row_index1, col] = inputs1[col]
            st.experimental_rerun()

    st.divider()
    # Exibindo Dataframe 2
    st.subheader("Tabela de Ingredientes")
    st.table(st.session_state.df2)
    options2 = ['Adicionar Nova Linha'] + [f'Linha {i}' for i in range(len(st.session_state.df2))]
    selected_option2 = st.selectbox('Selecione uma linha para editar ou adicione uma nova', options2, key='df2_select')
    if selected_option2 == 'Adicionar Nova Linha':
        inputs2 = create_inputs(st.session_state.df2)
        col1, col2 = st.columns(2)
        with col1:
            btn_add2 = st.button('Adicionar')
        
        if btn_add2:
            new_row2 = pd.DataFrame([inputs2])
            st.session_state.df2 = pd.concat([st.session_state.df2, new_row2], ignore_index=True)
            st.experimental_rerun()
    else:
        row_index2 = int(selected_option2.split(' ')[1])
        row_data2 = st.session_state.df2.iloc[row_index2]
        inputs2 = create_inputs(st.session_state.df2, row=row_data2)
        col1, col2 = st.columns(2)
        with col1:
            btn_update2 = st.button('Editar')
        
        if btn_update2:
            for col in st.session_state.df2.columns:
                st.session_state.df2.at[row_index2, col] = inputs2[col]
            st.experimental_rerun()

    # Exibir o Dataframe 3
    st.subheader("Tabela de Valor Nutricional")
    st.table(st.session_state.df3)   
    # Selecionando a linha para editar ou adicionar uma nova linha
    options3 = [f'Linha {i}' for i in range(len(st.session_state.df3))]
    selected_option3 = st.selectbox('Edite os detalhes principais de sua receita', options3, key='df3_select')
    
    if selected_option3:
        row_index3 = int(selected_option3.split(' ')[1])
        row_data3 = st.session_state.df3.iloc[row_index3]
        inputs3 = create_inputs(st.session_state.df3, row=row_data3)
        col1, col2 = st.columns(2)
        with col1:
            btn_update3 = st.button('Atualizar Valor Nutricional')
            
        if btn_update3:
            for col in st.session_state.df3.columns:
                st.session_state.df3.at[row_index3, col] = inputs3[col]
            st.experimental_rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('Baixar como PDF'):
            pdf_buffer = create_pdf(st.session_state.df1, st.session_state.df2, st.session_state.df3, st.session_state.preparo_str)
            st.download_button(label="Baixar PDF", data=pdf_buffer, file_name=f"ficha_técnica_{st.session_state.nome_receita}.pdf", mime="application/pdf")
    with col2:
        if st.button('Baixar em CSV'):
            st.markdown('CSV Ainda não implementado, aguarde atualizações!')
    with col3:
        if st.button('Baixar em XLSX'):
            st.markdown('XLSX Ainda não implementado, aguarde atualizações!')


