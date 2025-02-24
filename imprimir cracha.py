import barcode
from barcode.writer import ImageWriter

# Verifique se "code128" está disponível
barcode_type = barcode.get_barcode_class("code128")

if barcode_type is None:
    print("Erro: O tipo de código de barras 'code128' não está disponível!")
else:
    # Número do funcionário (ID)
    employee_id = "2034"

    # Criar código de barras
    employee_barcode = barcode_type(employee_id, writer=ImageWriter())

    # Salvar como imagem
    filename = employee_barcode.save("cracha_2034")

    print(f"✅ Crachá gerado com sucesso: {filename}.png")
