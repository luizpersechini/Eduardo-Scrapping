import pandas as pd

df = pd.read_excel('input_cnpjs_retry.xlsx')
print(f'📊 Total de CNPJs para retry: {len(df)}')
print(f'⏱️  Tempo estimado: ~{len(df) * 68} segundos ({len(df) * 68 / 60:.1f} minutos)')
print('\n📋 Lista de CNPJs:')
for i, cnpj in enumerate(df['CNPJ'], 1):
    print(f'  {i:2d}. {cnpj}')

