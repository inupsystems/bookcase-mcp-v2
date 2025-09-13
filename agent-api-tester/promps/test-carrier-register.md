# 🚀 PROMPT DE TESTE - AGENT API TESTER (CARRIERS)

Execute os seguintes testes sequenciais usando as ferramentas de Carrier disponíveis:

---

**TESTE COMPLETO DAS FERRAMENTAS MCP - CARRIER API TESTER**

Execute os seguintes testes sequenciais usando as ferramentas disponíveis:

🔹 **Teste 1 - Filtrar Carriers**
- Ferramenta: `filter`
- Parâmetros: `{"limit": 5}`
- Objetivo: Verificar listagem básica de carriers

🔹 **Teste 2 - Buscar Carrier Específico**  
- Ferramenta: `getCarrierById`
- Parâmetros: `{"id": 1}` (ajuste o ID conforme existente no sistema)
- Objetivo: Testar busca por ID

🔹 **Teste 3 - Criar Novo Carrier**
- Ferramenta: `createCarrier`
- Parâmetros: `{"name": "Carrier Teste MCP", "document": "12345678901", "status": "ACTIVE"}`
- Objetivo: Testar criação de novo carrier

🔹 **Teste 4 - Atualizar Carrier**
- Ferramenta: `updateCarrier`
- Parâmetros: `{"id": 1, "name": "Carrier Atualizado", "status": "INACTIVE"}`
- Objetivo: Testar modificação de carrier existente

🔹 **Teste 5 - Deletar Carrier**
- Ferramenta: `deleteCarrier`
- Parâmetros: `{"id": 1}`
- Objetivo: Testar remoção de carrier (executar por último ou usar ID criado no teste 3)

**PARA CADA TESTE, REPORTE:**
- ✅ Status (sucesso/erro)
- ⏱️ Tempo de resposta (se possível)
- 📊 Dados retornados (resumo)
- 🔧 Problemas encontrados
- 📝 ID do carrier criado (para testes subsequentes)

**FERRAMENTAS DISPONÍVEIS:**
- `filter` - GET /carriers/filter (listar carriers)
- `getCarrierById` - Buscar carrier por ID
- `createCarrier` - Criar novo carrier
- `updateCarrier` - Atualizar carrier existente
- `deleteCarrier` - Remover carrier

**NOTAS IMPORTANTES:**
1. Ajuste os IDs conforme a realidade do banco de dados
2. Para o teste de delete, considere criar um carrier primeiro e depois deletá-lo
3. Os parâmetros podem variar conforme a API real - ajuste conforme documentação

Execute todos os testes e reporte os resultados de forma organizada.