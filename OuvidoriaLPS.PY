import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import mysql.connector
from mysql.connector import Error

# Teste de conexão inicial
try:
    conexao = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='admin',
        database='ouvidoria_db'
    )
    if conexao.is_connected():
        print(" Conexão bem-sucedida com o banco de dados!")
        conexao.close()
    else:
        print(" Não foi possível conectar.")
except Error as erro:
    print(f" Erro ao conectar ao banco: {erro}")

class OuvidoriaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OUVIDORIA")
        self.root.geometry("400x750")
        self.root.configure(bg="white")

        self.forma_envio = tk.StringVar(value="FE: NORMAL!")
        self.anexo_path = None

        self.build_interface()

    def build_interface(self):
        header = tk.Frame(self.root, bg="lightgray")
        header.pack(fill=tk.X)

        title_label = tk.Label(header, text="OUVIDORIA", bg="lightgray", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        btn_frame = tk.Frame(self.root, bg="white")
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        menu_btn = tk.Button(btn_frame, text="MENU", width=10, height=2, command=self.abrir_menu)
        menu_btn.pack(side=tk.LEFT)

        historico_btn = tk.Button(btn_frame, text="HISTÓRICO", width=10, height=2, command=self.abrir_historico)
        historico_btn.pack(side=tk.RIGHT)

        escrever_frame = tk.LabelFrame(self.root, text="ESCREVER", bg="white", padx=10, pady=10)
        escrever_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(escrever_frame, text="TÍTULO:", bg="white", anchor="w").pack(fill=tk.X)
        self.titulo_entry = tk.Entry(escrever_frame)
        self.titulo_entry.pack(fill=tk.X, pady=5)

        tk.Label(escrever_frame, text="DESCRIÇÃO:", bg="white", anchor="w").pack(fill=tk.X)
        self.descricao_text = tk.Text(escrever_frame, height=6)
        self.descricao_text.pack(fill=tk.X, pady=5)

        self.arquivo_label = tk.Label(escrever_frame, text="ADICIONAR ARQUIVO +", fg="blue", bg="white", cursor="hand2")
        self.arquivo_label.pack(anchor=tk.W, pady=5)
        self.arquivo_label.bind("<Button-1>", self.selecionar_anexo)

        envio_frame = tk.Frame(self.root, bg="white")
        envio_frame.pack(fill=tk.X, padx=20, pady=(10, 30))

        envio_label = tk.Label(envio_frame, text="FORMA DE ENVIO", font=("Arial", 10, "bold"), bg="lightgray", anchor="w")
        envio_label.pack(anchor=tk.E)

        envio_menu = ttk.OptionMenu(envio_frame, self.forma_envio, self.forma_envio.get(), "FE: NORMAL!", "FE: ANÔNIMA!")
        envio_menu.pack(anchor=tk.E, pady=2)

        enviar_btn = tk.Button(self.root, text="ENVIAR", bg="white", padx=10, pady=5, command=self.enviar)
        enviar_btn.pack(pady=30)

    def selecionar_anexo(self, event=None):
        filetypes = [("Imagens e Vídeos", "*.png *.jpg *.jpeg *.mp4 *.mov *.avi")]
        path = filedialog.askopenfilename(title="Selecionar Arquivo", filetypes=filetypes)
        if path:
            self.anexo_path = path
            self.arquivo_label.config(text="Arquivo: " + path.split("/")[-1], fg="black")
        else:
            self.anexo_path = None
            self.arquivo_label.config(text="ADICIONAR ARQUIVO +", fg="blue")

    def enviar(self):
        titulo = self.titulo_entry.get().strip()
        descricao = self.descricao_text.get("1.0", tk.END).strip()
        envio = self.forma_envio.get()
        anexo = self.anexo_path if self.anexo_path else ""

        if not titulo or not descricao:
            messagebox.showerror("Erro", "Preencha os campos de TÍTULO e DESCRIÇÃO.")
            return

        # Salva no banco de dados
        self.salvar_no_banco(titulo, descricao, envio, anexo)
        
        # Mantém a funcionalidade original de salvar em JSON
        self.salvar_em_historico({
            "titulo": titulo,
            "descricao": descricao,
            "envio": envio,
            "anexo": anexo
        })

        msg = f"Envio {'anônimo' if envio == 'FE: ANÔNIMA!' else 'normal'} realizado com sucesso!"
        msg += f"\nArquivo: {anexo.split('/')[-1]}" if anexo else "\nNenhum arquivo anexado."
        messagebox.showinfo("Sucesso", msg)

        self.limpar_formulario()

    def salvar_no_banco(self, titulo, descricao, envio, anexo):
        try:
            conexao = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="admin",
                database="ouvidoria_db"
            )

            if conexao.is_connected():
                cursor = conexao.cursor()

                cursor.execute("""
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    titulo VARCHAR(255),
                    descricao TEXT,
                    envio VARCHAR(50),
                    anexo VARCHAR(255),
                    data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                sql = "INSERT INTO mensagens (titulo, descricao, envio, anexo) VALUES (%s, %s, %s, %s)"
                valores = (titulo, descricao, envio, anexo)
                cursor.execute(sql, valores)
                conexao.commit()

        except Error as e:
            print(f"Erro ao conectar ou inserir dados: {e}")
            # Mantém o arquivo JSON como fallback
            messagebox.showwarning("Aviso", "Dados salvos localmente (falha ao conectar ao banco)")

        finally:
            if 'conexao' in locals() and conexao.is_connected():
                cursor.close()
                conexao.close()

    def limpar_formulario(self):
        self.titulo_entry.delete(0, tk.END)
        self.descricao_text.delete("1.0", tk.END)
        self.anexo_path = None
        self.arquivo_label.config(text="ADICIONAR ARQUIVO +", fg="blue")
        self.forma_envio.set("FE: NORMAL!")

    def salvar_em_historico(self, dados):
        historico = []

        if os.path.exists("historico.json"):
            with open("historico.json", "r") as f:
                try:
                    historico = json.load(f)
                except json.JSONDecodeError:
                    historico = []

        historico.append(dados)

        with open("historico.json", "w") as f:
            json.dump(historico, f, indent=4)

    def abrir_historico(self):
        historico_window = tk.Toplevel(self.root)
        historico_window.title("Histórico de Mensagens")
        historico_window.geometry("400x500")

        notebook = ttk.Notebook(historico_window)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Aba do banco de dados
        frame_db = ttk.Frame(notebook)
        notebook.add(frame_db, text="Banco de Dados")

        text_db = tk.Text(frame_db, wrap=tk.WORD)
        scroll_db = ttk.Scrollbar(frame_db, command=text_db.yview)
        text_db.configure(yscrollcommand=scroll_db.set)
        
        scroll_db.pack(side=tk.RIGHT, fill=tk.Y)
        text_db.pack(fill=tk.BOTH, expand=True)

        try:
            conexao = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="admin",
                database="ouvidoria_db"
            )
            
            if conexao.is_connected():
                cursor = conexao.cursor()
                cursor.execute("SELECT * FROM mensagens ORDER BY data_envio DESC")
                resultados = cursor.fetchall()
                
                for idx, item in enumerate(resultados, 1):
                    texto = f"{idx}. [{item[3]}] {item[1]}\nData: {item[5]}\nDescrição: {item[2]}\n"
                    if item[4]:
                        texto += f"Anexo: {item[4]}\n"
                    texto += "-" * 30 + "\n"
                    text_db.insert(tk.END, texto)
                
                conexao.close()
        except Error as e:
            text_db.insert(tk.END, f"Erro ao acessar o banco de dados: {e}")

        # Aba do arquivo JSON (mantendo funcionalidade original)
        frame_json = ttk.Frame(notebook)
        notebook.add(frame_json, text="Arquivo Local")

        text_json = tk.Text(frame_json, wrap=tk.WORD)
        scroll_json = ttk.Scrollbar(frame_json, command=text_json.yview)
        text_json.configure(yscrollcommand=scroll_json.set)
        
        scroll_json.pack(side=tk.RIGHT, fill=tk.Y)
        text_json.pack(fill=tk.BOTH, expand=True)

        if os.path.exists("historico.json"):
            with open("historico.json", "r") as f:
                try:
                    historico = json.load(f)
                    for idx, item in enumerate(historico, 1):
                        texto = f"{idx}. [{item['envio']}] {item['titulo']}\nDescrição: {item['descricao']}\n"
                        if item['anexo']:
                            texto += f"Anexo: {item['anexo']}\n"
                        texto += "-" * 30 + "\n"
                        text_json.insert(tk.END, texto)
                except json.JSONDecodeError:
                    text_json.insert(tk.END, "Erro ao carregar o histórico local.")
        else:
            text_json.insert(tk.END, "Nenhum registro local encontrado.")

    def abrir_menu(self):
        menu_window = tk.Toplevel(self.root)
        menu_window.title("MENU")
        menu_window.geometry("400x500")
        menu_window.configure(bg="white")

        tk.Label(menu_window, text="CADASTRO", font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        # E-mail
        tk.Label(menu_window, text="E-mail:", bg="white").pack(anchor=tk.W, padx=20)
        email_entry = tk.Entry(menu_window, width=40)
        email_entry.pack(pady=5)

        # Senha
        tk.Label(menu_window, text="Senha:", bg="white").pack(anchor=tk.W, padx=20)
        senha_entry = tk.Entry(menu_window, show="*", width=40)
        senha_entry.pack(pady=5)

        # Confirmar senha
        tk.Label(menu_window, text="Confirmar Senha:", bg="white").pack(anchor=tk.W, padx=20)
        confirmar_entry = tk.Entry(menu_window, show="*", width=40)
        confirmar_entry.pack(pady=5)

        # Botão Cadastrar
        def cadastrar():
            email = email_entry.get()
            senha = senha_entry.get()
            confirmar = confirmar_entry.get()

            if not email or not senha or not confirmar:
                messagebox.showwarning("Atenção", "Preencha todos os campos.")
            elif senha != confirmar:
                messagebox.showerror("Erro", "As senhas não coincidem.")
            else:
                try:
                    conexao = mysql.connector.connect(
                        host="127.0.0.1",
                        user="root",
                        password="admin",
                        database="ouvidoria_db"
                    )
                    
                    if conexao.is_connected():
                        cursor = conexao.cursor()
                        
                        # Verifica se a tabela de usuários existe
                        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS usuarios (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            email VARCHAR(255) UNIQUE,
                            senha VARCHAR(255),
                            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """)
                        
                        # Verifica se o usuário já existe
                        cursor.execute("SELECT email FROM usuarios WHERE email = %s", (email,))
                        if cursor.fetchone():
                            messagebox.showerror("Erro", "Este e-mail já está cadastrado!")
                        else:
                            # Insere o novo usuário
                            cursor.execute("INSERT INTO usuarios (email, senha) VALUES (%s, %s)", (email, senha))
                            conexao.commit()
                            messagebox.showinfo("Sucesso", f"Usuário {email} cadastrado com sucesso!")
                    
                    conexao.close()
                except Error as e:
                    messagebox.showerror("Erro", f"Não foi possível completar o cadastro: {e}")

        tk.Button(menu_window, text="Cadastrar", bg="#4CAF50", fg="white", command=cadastrar).pack(pady=10)

        # Separador
        ttk.Separator(menu_window, orient="horizontal").pack(fill=tk.X, pady=20)

        # Login
        def fazer_login():
            email = email_entry.get()
            senha = senha_entry.get()
            
            if not email or not senha:
                messagebox.showwarning("Atenção", "Preencha e-mail e senha.")
                return
            
            try:
                conexao = mysql.connector.connect(
                    host="127.0.0.1",
                    user="root",
                    password="admin",
                    database="ouvidoria_db"
                )
                
                if conexao.is_connected():
                    cursor = conexao.cursor()
                    cursor.execute("SELECT * FROM usuarios WHERE email = %s AND senha = %s", (email, senha))
                    usuario = cursor.fetchone()
                    
                    if usuario:
                        messagebox.showinfo("Sucesso", f"Bem-vindo, {email}!")
                        menu_window.destroy()
                    else:
                        messagebox.showerror("Erro", "E-mail ou senha incorretos!")
                
                conexao.close()
            except Error as e:
                messagebox.showerror("Erro", f"Não foi possível conectar ao banco: {e}")

        tk.Button(menu_window, text="Fazer Login", bg="#2196F3", fg="white", command=fazer_login).pack(pady=5)

        # Recuperar senha
        def recuperar_senha():
            email = email_entry.get()
            if not email:
                messagebox.showwarning("Atenção", "Digite seu e-mail para recuperar a senha.")
                return
            
            messagebox.showinfo("Recuperação", f"Instruções de recuperação enviadas para {email}")

        tk.Button(menu_window, text="Esqueci minha senha", bg="#f44336", fg="white", command=recuperar_senha).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = OuvidoriaApp(root)
    root.mainloop()
