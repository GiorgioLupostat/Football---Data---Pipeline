import pandas as pd
import matplotlib.pyplot as plt
from adjustText import adjust_text


nome_file = 'SerieB2526.xlsx'
df = pd.read_excel(nome_file) 


if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.droplevel(0)


df['Min'] = df['Min'].astype(str).str.replace('.', '', regex=False)


df['Age'] = pd.to_numeric(df['Age'], errors='coerce')
df['Min'] = pd.to_numeric(df['Min'], errors='coerce')
df['Gls'] = pd.to_numeric(df['Gls'], errors='coerce')
df['Ast'] = pd.to_numeric(df['Ast'], errors='coerce')


df_filtrato = df[
    (df['Nation'].astype(str).str.contains('ITA', na=False)) &
    (df['Age'] <= 22) &
    (df['Min'] >= 400) &
    (df['Pos'].astype(str).str.contains('FW|MF', regex=True))
].copy()


df_filtrato['Gol_P90'] = (df_filtrato['Gls'] / df_filtrato['Min']) * 90
df_filtrato['Ast_P90'] = (df_filtrato['Ast'] / df_filtrato['Min']) * 90


plt.figure(figsize=(14, 10))


media_gol = df_filtrato['Gol_P90'].mean()
media_ast = df_filtrato['Ast_P90'].mean()


plt.scatter(df_filtrato['Gol_P90'], df_filtrato['Ast_P90'], color='#2A4B7C', s=100)


plt.axvline(x=media_gol, color='red', linestyle='--', alpha=0.5, label=f'Media Gol P90: {media_gol:.2f}')
plt.axhline(y=media_ast, color='green', linestyle='--', alpha=0.5, label=f'Media Assist P90: {media_ast:.2f}')


testi = []
for i, row in df_filtrato.iterrows():
    testi.append(plt.text(row['Gol_P90'], row['Ast_P90'], row['Player'], fontsize=9))


adjust_text(testi, arrowprops=dict(arrowstyle="-", color='gray', lw=0.5))


plt.title('Scouting Talenti U22 Italiani - Serie B (Assist vs Gol)', fontsize=16, fontweight='bold')
plt.xlabel('Gol Segnati per 90 minuti (Gol P90)', fontsize=12)
plt.ylabel('Assist Forniti per 90 minuti (Ast P90)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()

plt.show()