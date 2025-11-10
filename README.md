<div align="center">

# 🚀 Hyperliquid MCP Server

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0%2B-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hyperliquid](https://img.shields.io/badge/Hyperliquid-DEX-purple.svg)](https://hyperliquid.xyz)

**Conecte Claude Code ao poder da Hyperliquid DEX**

Desenvolvido por **Caio Vicentino** com **Claude Code**

*Para as comunidades: Yield Hacker, Renda Cripto e Cultura Builder*

[Instalação](#-instalação) • [Recursos](#-recursos) • [Exemplos](#-exemplos-de-uso) • [Documentação](#-documentação-completa) • [FAQ](#-faq)

</div>

---

## 📖 O que é este projeto?

O **Hyperliquid MCP Server** é uma implementação completa do [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) da Anthropic que permite ao **Claude Desktop** interagir diretamente com a exchange descentralizada **Hyperliquid**.

Com este servidor MCP, você pode:
- 💬 **Tradear usando linguagem natural** através do Claude
- 📊 **Analisar mercados** com dados em tempo real
- 🤖 **Automatizar estratégias** com a inteligência do Claude
- 🔐 **Manter controle total** das suas chaves e fundos

### O que é MCP?

**Model Context Protocol (MCP)** é um padrão criado pela Anthropic para conectar assistentes de IA (como Claude) a ferramentas e fontes de dados externas. Pense nele como "plugins" para Claude Desktop.

### O que é Hyperliquid?

**Hyperliquid** é uma exchange descentralizada (DEX) de alta performance para trading de futuros perpétuos, oferecendo:
- 📈 **Orderbook on-chain** com performance de CEX
- ⚡ **Execução de baixa latência**
- 💰 **Taxas competitivas** e funding rates
- 🔒 **Full self-custody** - você controla suas chaves
- 🎯 **Alavancagem até 50x** em diversos ativos

---

## ✨ Recursos

### 27 Ferramentas Poderosas em 4 Categorias

#### 📈 Trading (9 ferramentas)
- `place_order` - Ordens limit e market
- `place_batch_orders` - Múltiplas ordens em lote
- `cancel_order` - Cancelar ordem específica
- `cancel_all_orders` - Cancelar todas as ordens
- `modify_order` - Modificar preço/quantidade
- `place_twap_order` - Ordens TWAP para grande volume
- `adjust_leverage` - Ajustar alavancagem (cross/isolated)
- `modify_isolated_margin` - Gerenciar margem isolada
- `update_dead_mans_switch` - Sistema de segurança automático

#### 👤 Gerenciamento de Conta (8 ferramentas)
- `get_user_state` - Estado completo da conta
- `get_positions` - Posições abertas com PnL
- `get_open_orders` - Ordens abertas
- `get_user_fills` - Histórico de trades
- `get_historical_orders` - Histórico de ordens
- `get_portfolio_value` - Análise completa do portfólio
- `get_subaccounts` - Gerenciar subcontas
- `get_rate_limit_status` - Status de rate limits

#### 📊 Dados de Mercado (6 ferramentas)
- `get_all_mids` - Preços mid de todos os pares
- `get_l2_orderbook` - Order book L2 em tempo real
- `get_candles` - Dados históricos (OHLCV)
- `get_recent_trades` - Trades recentes
- `get_funding_rates` - Taxas de funding
- `get_asset_contexts` - Contexto e estatísticas de mercado

#### 🔄 WebSocket em Tempo Real (4 ferramentas)
- `subscribe_user_events` - Eventos da conta
- `subscribe_market_data` - Dados de mercado live
- `subscribe_order_updates` - Atualizações de ordens
- `get_active_subscriptions` - Gerenciar assinaturas

---

## 🚀 Instalação

### Pré-requisitos

- **Python 3.8+** instalado
- **Claude Desktop** instalado ([baixar aqui](https://claude.ai/download))
- **Conta Hyperliquid** com credenciais de API
- **macOS, Linux ou Windows**

### Instalação Rápida (Recomendado)

1. **Clone ou baixe este repositório**
   ```bash
   git clone https://github.com/seu-usuario/hyperliquid-mcp-server.git
   cd hyperliquid-mcp-server
   ```

2. **Execute o script de instalação automática**
   ```bash
   python3 setup.py
   ```

   O script irá:
   - ✅ Criar ambiente virtual Python
   - ✅ Instalar todas as dependências
   - ✅ Gerar arquivos de configuração
   - ✅ Configurar Claude Desktop automaticamente
   - ✅ Guiá-lo através da configuração de credenciais

3. **Configure suas credenciais**

   Edite o arquivo `.env` criado:
   ```bash
   nano .env
   ```

   Adicione suas credenciais da Hyperliquid:
   ```env
   HYPERLIQUID_PRIVATE_KEY=0x...
   HYPERLIQUID_ACCOUNT_ADDRESS=0x...
   HYPERLIQUID_NETWORK=mainnet
   ```

4. **Reinicie o Claude Desktop**

   Feche completamente e reabra o Claude Desktop.

5. **Verifique a instalação**

   No Claude, pergunte:
   ```
   Quais ferramentas da Hyperliquid você tem disponíveis?
   ```

### Instalação Manual (Avançado)

<details>
<summary>Clique para expandir instruções manuais</summary>

```bash
# 1. Criar ambiente virtual
python3 -m venv venv

# 2. Ativar ambiente virtual
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Copiar template de configuração
cp .env.example .env

# 5. Editar .env com suas credenciais
nano .env

# 6. Configurar Claude Desktop
# Adicione ao arquivo de configuração do Claude:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Linux: ~/.config/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

{
  "mcpServers": {
    "hyperliquid": {
      "command": "/caminho/completo/para/venv/bin/python",
      "args": ["/caminho/completo/para/server.py"],
      "env": {
        "HYPERLIQUID_PRIVATE_KEY": "sua_chave_privada",
        "HYPERLIQUID_ACCOUNT_ADDRESS": "seu_endereco"
      }
    }
  }
}
```

</details>

---

## 🔑 Obtendo Suas Credenciais

### 1. Private Key (Chave Privada)

Exporte sua private key da carteira (MetaMask, Trust Wallet, etc.):
- Deve estar no formato `0x...` (64 caracteres hexadecimais após o 0x)
- **NUNCA compartilhe esta chave com ninguém**
- Mantenha em local seguro

### 2. Account Address (Endereço da Conta)

Seu endereço Ethereum (também formato `0x...`):
- Endereço público da sua carteira
- Visível publicamente on-chain

### ⚠️ Segurança das Credenciais

- 🔒 Armazene credenciais apenas no arquivo `.env`
- ❌ **NUNCA** faça commit do `.env` no git
- 🧪 Use **testnet** para testes iniciais
- 🔄 Rotacione chaves periodicamente
- 💼 Use carteiras separadas para trading/holding

---

## 💡 Exemplos de Uso

Uma vez instalado, você pode interagir com a Hyperliquid através de linguagem natural no Claude Desktop:

### 📈 Trading

**Colocar Ordem Limit**
```
Você: "Coloque uma ordem de compra de 0.1 BTC a $45,000"

Claude irá:
✅ Validar sua solicitação
✅ Colocar a ordem
✅ Confirmar com order ID e status
```

**Ordem Market**
```
Você: "Compre 0.5 ETH a mercado"

Claude irá:
✅ Executar ordem imediatamente
✅ Mostrar preço de execução e taxas
✅ Atualizar sua posição
```

**Cancelar Ordens**
```
Você: "Cancele todas minhas ordens de BTC"

Claude irá usar: cancel_all_orders
✅ Cancelar todas as ordens de BTC
✅ Mostrar resumo de cancelamento
```

**Batch Trading**
```
Você: "Coloque 5 ordens de compra de ETH de $3000 a $2900 em intervalos de $25"

Claude irá usar: place_batch_orders
✅ Criar grid de ordens
✅ Executar em única transação
✅ Confirmar todas as ordens
```

### 💰 Gerenciamento de Posições

**Verificar Posições**
```
Você: "Quais são minhas posições abertas e seus PnLs?"

Claude mostrará:
📊 Todas as posições abertas
💵 Preços de entrada
📈 PnL (realizado e não realizado)
⚡ Alavancagem utilizada
⚠️ Preços de liquidação
```

**Fechar Posição**
```
Você: "Feche minha posição de ETH a mercado"

Claude irá:
✅ Fechar posição inteira
✅ Mostrar preço de saída
✅ Calcular PnL final
```

**Ajustar Alavancagem**
```
Você: "Configure alavancagem de 10x para trades de BTC"

Claude irá:
✅ Atualizar configuração de leverage
✅ Mostrar requisitos de margem
✅ Avisar sobre riscos
```

### 📊 Análise de Mercado

**Preços Atuais**
```
Você: "Qual o preço atual do BTC na Hyperliquid?"

Claude mostrará:
💰 Preço bid/ask
📊 Mark price
🎯 Index price
📈 Spread atual
```

**Order Book**
```
Você: "Mostre o order book do ETH"

Claude mostrará:
📗 Níveis de bid
📕 Níveis de ask
💹 Liquidez em cada nível
📊 Análise de spread
```

**Dados Históricos**
```
Você: "Pegue candles de 1 hora do BTC das últimas 24 horas"

Claude retornará:
📈 Dados OHLCV
📊 Volume
🔍 Pode analisar padrões
```

### 📡 Dados em Tempo Real (WebSocket)

**Monitorar Order Book**
```
Você: "Inscreva no order book do BTC e me alerte sobre ordens grandes"

Claude irá:
✅ Conectar ao WebSocket
✅ Stream do order book em tempo real
✅ Monitorar atividade de "baleias"
✅ Alertar sobre mudanças significativas
```

**Acompanhar Trades**
```
Você: "Monitore trades de ETH em tempo real"

Claude irá:
✅ Feed de trades ao vivo
✅ Analisar fluxo de compra/venda
✅ Detectar atividade incomum
```

### 🤖 Estratégias Avançadas

**Estratégia Condicional**
```
Você: "Se BTC cair abaixo de $44,000, compre 0.2 BTC com alavancagem 5x"

Claude irá:
1️⃣ Monitorar preço (subscribe_market_data)
2️⃣ Quando acionado, ajustar leverage
3️⃣ Colocar ordem
4️⃣ Confirmar execução
```

**Análise de Portfólio**
```
Você: "Analise o risco do meu portfólio atual"

Claude irá:
1️⃣ Buscar posições (get_positions)
2️⃣ Verificar saldo (get_user_state)
3️⃣ Calcular exposição por ativo
4️⃣ Avaliar utilização de margem
5️⃣ Recomendar ajustes
```

**Market Making**
```
Você: "Coloque ordens nos dois lados do ETH com spread de 1%, 0.1 ETH cada"

Claude irá usar: place_batch_orders
✅ Ordens simultâneas de compra/venda
✅ Configurar grid de market making
✅ Monitorar e ajustar
```

---

## 🛠️ Configuração Avançada

### Variáveis de Ambiente

Todas as configurações são gerenciadas pelo arquivo `.env`:

```bash
# Credenciais (OBRIGATÓRIO)
HYPERLIQUID_PRIVATE_KEY=0x...        # Chave privada Ethereum
HYPERLIQUID_ACCOUNT_ADDRESS=0x...    # Endereço da carteira

# Rede
HYPERLIQUID_NETWORK=mainnet          # ou 'testnet'

# Endpoints (configurado automaticamente baseado na rede)
HYPERLIQUID_API_URL=https://api.hyperliquid.xyz
HYPERLIQUID_WS_URL=wss://api.hyperliquid.xyz/ws

# Configurações Opcionais
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
RATE_LIMIT_WEIGHT=1200              # Max API weight por minuto
HTTP_TIMEOUT=30                     # Timeout HTTP (segundos)
WS_TIMEOUT=60                       # Timeout WebSocket (segundos)
```

### Testnet vs Mainnet

**Para Desenvolvimento/Testes:**
```bash
HYPERLIQUID_NETWORK=testnet
HYPERLIQUID_API_URL=https://api.hyperliquid-testnet.xyz
HYPERLIQUID_WS_URL=wss://api.hyperliquid-testnet.xyz/ws
```

**Para Trading Real:**
```bash
HYPERLIQUID_NETWORK=mainnet
HYPERLIQUID_API_URL=https://api.hyperliquid.xyz
HYPERLIQUID_WS_URL=wss://api.hyperliquid.xyz/ws
```

⚠️ **ATENÇÃO:** Sempre teste em testnet primeiro!

---

## 🔒 Segurança

### Gerenciamento de Chaves API

#### ✅ FAÇA:
- Armazene chaves apenas no `.env`
- Use testnet para desenvolvimento
- Rotacione chaves periodicamente
- Configure whitelists de saques
- Use margem isolada para trades arriscados
- Mantenha backups seguros das chaves

#### ❌ NÃO FAÇA:
- Commitar `.env` no git
- Compartilhar chaves em logs ou mensagens de erro
- Usar chaves de mainnet em desenvolvimento
- Armazenar chaves diretamente no código
- Compartilhar sua private key com ninguém

### Segurança da Private Key

Sua private key tem **controle total** sobre sua conta:
- 🔐 Trate como uma senha bancária
- 🚫 Nunca compartilhe com ninguém
- 💾 Mantenha backups em locais seguros
- 🔧 Considere usar hardware wallet
- 👥 Use contas separadas para trading/holding

### Dead Man's Switch

Configure um sistema de segurança automático:
```
"Configure dead man's switch para 300 segundos"
```

Se você não atualizar o switch no prazo:
- ⚠️ **TODAS** as ordens abertas serão canceladas automaticamente
- 🛡️ Proteção contra perda de conectividade
- 🔒 Segurança adicional para sua conta

---

## 🐛 Troubleshooting

### Problemas Comuns

<details>
<summary><b>❌ "MCP server não encontrado no Claude Desktop"</b></summary>

**Soluções:**
1. Verifique que o Claude Desktop foi fechado completamente antes da instalação
2. Confirme que `claude_desktop_config.json` está no local correto:
   - macOS: `~/Library/Application Support/Claude/`
   - Linux: `~/.config/Claude/`
   - Windows: `%APPDATA%\Claude\`
3. Reinicie Claude Desktop completamente (Quit, não apenas fechar janela)
4. Verifique logs em `~/Library/Logs/Claude/`

</details>

<details>
<summary><b>❌ "Authentication failed"</b></summary>

**Soluções:**
1. Verifique que `.env` tem credenciais corretas
2. Confirme formato da private key (deve começar com `0x`)
3. Certifique-se que account address corresponde à private key
4. Teste credenciais com chamada API simples
5. Verifique se está usando rede correta (testnet/mainnet)

</details>

<details>
<summary><b>❌ "Rate limit exceeded"</b></summary>

**Soluções:**
1. Reduza frequência de requisições
2. Use WebSocket subscriptions em vez de polling
3. Agrupe operações relacionadas
4. Ajuste `RATE_LIMIT_WEIGHT` no `.env`
5. Verifique status com `get_rate_limit_status`

</details>

<details>
<summary><b>❌ "Order placement failed"</b></summary>

**Soluções:**
1. Verifique margem disponível suficiente
2. Confirme que leverage está configurado
3. Certifique-se que tamanho da ordem atende mínimo
4. Valide que preço está dentro de limites razoáveis
5. Verifique se mercado está em horário de trading

</details>

<details>
<summary><b>❌ "WebSocket disconnected"</b></summary>

**Soluções:**
1. Verifique conectividade de rede
2. Confirme WebSocket URL correto
3. Certifique-se que firewall permite WebSocket
4. Reinicie o MCP server
5. Verifique logs para detalhes de erro

</details>

### Modo Debug

Ative logs detalhados editando `.env`:

```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

Isso mostrará:
- 📡 Todas as requisições/respostas de API
- 💬 Mensagens WebSocket
- ⏱️ Rastreamento de rate limits
- 🐛 Stack traces de erros

### Testando o Servidor

Teste o MCP server isoladamente:

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o inspetor MCP
mcp dev server.py

# Isso abre uma interface de teste interativa
```

---

## 📚 Documentação Completa

### APIs e SDKs

- **Hyperliquid Docs**: https://hyperliquid.gitbook.io/hyperliquid-docs/
- **Python SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **WebSocket API**: https://hyperliquid.gitbook.io/hyperliquid-docs/websocket-api
- **Trading Guide**: https://hyperliquid.gitbook.io/hyperliquid-docs/trading

### Model Context Protocol

- **MCP Specification**: https://modelcontextprotocol.io/
- **MCP SDK**: https://github.com/anthropics/mcp
- **Claude Desktop**: https://docs.anthropic.com/claude/docs/mcp

### Rate Limits

Hyperliquid implementa rate limiting baseado em sistema de pesos:

| Tipo | Weight | Limite |
|------|--------|--------|
| Market Data | 1-2 | 1200/min |
| Account Data | 2-5 | 1200/min |
| Trading | 5-10 | 1200/min |
| WebSocket | 0 | Ilimitado |

**Melhores Práticas:**
- ✅ Use WebSocket para dados em tempo real
- ✅ Agrupe operações quando possível
- ✅ Cache dados que não mudam frequentemente
- ✅ Monitore uso de rate limit

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas! Veja como adicionar novas ferramentas:

### Adicionando uma Nova Tool

1. **Defina a tool em `server.py`**

```python
@mcp.tool()
async def sua_nova_tool(param1: str, param2: int, ctx: Context = None) -> Dict[str, Any]:
    """
    Descrição da ferramenta para Claude.

    Args:
        param1: Descrição do parâmetro 1
        param2: Descrição do parâmetro 2

    Returns:
        Descrição do resultado
    """
    if ctx: ctx.info(f"Executando sua_nova_tool...")

    result = await app_context.sua_categoria.metodo(param1, param2)
    return result
```

2. **Atualize `mcp.json`**

```json
{
  "name": "sua_nova_tool",
  "description": "O que a ferramenta faz"
}
```

3. **Teste a ferramenta**

```bash
mcp dev server.py
```

4. **Envie um pull request**

### Diretrizes de Desenvolvimento

- ✅ Siga o estilo de código existente
- ✅ Adicione type hints
- ✅ Inclua docstrings
- ✅ Trate erros graciosamente
- ✅ Considere rate limits
- ✅ Teste completamente

---

## ❓ FAQ

<details>
<summary><b>É seguro usar com dinheiro real?</b></summary>

O servidor é open-source e usa SDKs oficiais da Hyperliquid. No entanto, trading sempre carrega riscos. **Sempre comece com testnet e pequenas quantias.**

</details>

<details>
<summary><b>Claude pode tradear automaticamente?</b></summary>

Claude pode executar trades quando você solicitar, mas **não irá tradear sem sua instrução explícita** para cada ação. Você mantém controle total.

</details>

<details>
<summary><b>Qual a diferença de usar Hyperliquid diretamente?</b></summary>

Este MCP permite interação com **linguagem natural** através do Claude, facilitando análise de mercados e execução de estratégias complexas. Claude pode ajudar a interpretar dados, sugerir trades e executar múltiplas operações coordenadas.

</details>

<details>
<summary><b>Preciso manter Claude Desktop aberto?</b></summary>

**Sim**, o MCP server roda como parte do Claude Desktop e requer que ele esteja em execução.

</details>

<details>
<summary><b>Posso usar múltiplas contas Hyperliquid?</b></summary>

Atualmente, uma conta por instalação. Suporte para múltiplas contas está no roadmap.

</details>

<details>
<summary><b>Quais são as taxas?</b></summary>

Aplicam-se as taxas padrão da Hyperliquid (maker/taker fees). O MCP server em si é **gratuito e open-source**.

</details>

<details>
<summary><b>Minha private key é segura?</b></summary>

Sua private key fica **apenas no arquivo `.env` na sua máquina local**. Nunca é enviada para nenhum lugar além da API oficial da Hyperliquid.

</details>

<details>
<summary><b>Posso usar em Windows/Linux?</b></summary>

**Sim!** O MCP server é compatível com Windows, macOS e Linux.

</details>

---

## 🗺️ Roadmap

Funcionalidades planejadas:

- [ ] Order types avançados (stop-loss, take-profit)
- [ ] Analytics e reporting de portfólio
- [ ] Ferramentas de gerenciamento de risco
- [ ] Estratégias de trading automatizadas
- [ ] Suporte para múltiplas contas
- [ ] Dashboard de métricas de performance
- [ ] Integração com backtesting
- [ ] Sistema de alertas para preços/posições
- [ ] Exportação de dados de trades para CSV
- [ ] Integração com TradingView

---

## 📜 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

```
MIT License

Copyright (c) 2025 Caio Vicentino

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ⚠️ Disclaimer

Este software é fornecido **"como está"**, sem garantias de qualquer tipo.

**Trading de criptomoedas carrega risco significativo.**

- 📉 Você pode perder todo seu capital investido
- ⚠️ Apenas trade com fundos que você pode perder
- 🎓 Educação e gestão de risco são essenciais
- 🔬 Sempre teste em testnet primeiro

**Os autores não são responsáveis por quaisquer perdas financeiras incorridas através do uso deste software.**

Use por sua conta e risco.

---

## 🙏 Agradecimentos

- **Anthropic** pelo Model Context Protocol e Claude
- **Hyperliquid Team** pela excelente DEX e API
- **Python MCP SDK Contributors**
- **Comunidades**: Yield Hacker, Renda Cripto e Cultura Builder
- **Comunidade Open Source**

---

## 💬 Suporte e Comunidade

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/hyperliquid-mcp-server/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/hyperliquid-mcp-server/discussions)
- **Hyperliquid Discord**: https://discord.gg/hyperliquid
- **MCP Support**: https://github.com/anthropics/mcp

---

## 👨‍💻 Sobre o Desenvolvedor

**Desenvolvido por Caio Vicentino com Claude Code**

Este projeto foi criado para democratizar o acesso a ferramentas profissionais de trading, permitindo que qualquer pessoa possa interagir com a Hyperliquid usando linguagem natural através do Claude.

**Dedicado às comunidades:**
- 🎯 **Yield Hacker** - Maximizando retornos DeFi
- 💰 **Renda Cripto** - Educação financeira em cripto
- 🏗️ **Cultura Builder** - Construindo o futuro com AI

---

<div align="center">

### 🚀 Desenvolvido com Claude Code + Hyperliquid

**Se este projeto foi útil, dê uma ⭐ no repositório!**

[⬆ Voltar ao topo](#-hyperliquid-mcp-server)

</div>

---

## 📸 Screenshots

### Exemplo de Trading no Claude
```
Você: "Mostre minhas posições abertas e calcule meu PnL total"

Claude: Deixe-me buscar suas posições atuais...

📊 POSIÇÕES ABERTAS:

1. BTC-PERP
   • Tamanho: 0.5 BTC (Long)
   • Preço de Entrada: $45,230.00
   • Preço Atual: $46,150.00
   • PnL não realizado: +$460.00 (+2.03%)
   • Alavancagem: 5x
   • Liquidação: $38,500.00

2. ETH-PERP
   • Tamanho: 10 ETH (Long)
   • Preço de Entrada: $2,420.00
   • Preço Atual: $2,485.00
   • PnL não realizado: +$650.00 (+2.69%)
   • Alavancagem: 3x
   • Liquidação: $2,050.00

💰 RESUMO:
   • PnL Total não realizado: +$1,110.00
   • ROE médio: +2.36%
   • Margem utilizada: $8,450.00
   • Margem disponível: $11,550.00
```

### Exemplo de Análise de Mercado
```
Você: "Analise o mercado de BTC e sugira uma estratégia"

Claude: Vou analisar o mercado de BTC para você...

📊 ANÁLISE DE MERCADO - BTC

Preços Atuais:
• Preço Mark: $46,150.00
• Bid: $46,148.00 / Ask: $46,152.00
• Spread: $4.00 (0.009%)

Order Book:
• Suporte forte em: $46,000 (150 BTC)
• Resistência em: $46,500 (200 BTC)
• Liquidez: Excelente (spread tight)

Funding:
• Rate atual: 0.0085% (8h)
• Rate anualizado: +9.29%
• Próximo funding: em 3h 24min

Volume 24h:
• Volume: $2.4B
• Trades: 45,230
• Sentimento: Bullish (65% compra)

💡 SUGESTÃO DE ESTRATÉGIA:

Dado o funding positivo e resistência próxima, sugiro:

1. ENTRY: Ordem limit em $46,000 (suporte forte)
2. TAMANHO: 0.2 BTC (risco moderado)
3. ALAVANCAGEM: 3-5x
4. STOP LOSS: $45,700 (abaixo do suporte)
5. TAKE PROFIT: $46,800 (acima da resistência)

Risk/Reward: 1:2.66 (favorável)

Quer que eu execute esta estratégia?
```

---

**Happy Trading! 📈🚀**
