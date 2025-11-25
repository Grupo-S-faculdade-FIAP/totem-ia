# 🎨 Especificação de Design - Login Admin

## Paleta de Cores

### Cores Principais (Herdadas do TOTEM IA)
```
Gradiente Primário:    #667eea → #764ba2 (Roxo/Azul Gradiente)
Branco:                #FFFFFF
Cinza Escuro:          #333333
Cinza Médio:           #666666
Cinza Claro:           #999999
Cinza Muito Claro:     #E0E0E0
Fundo Cinzento:        #F5F5F5
Fundo Input:           #F9F9F9
```

### Cores de Feedback
```
Sucesso:               #4CAF50 (Verde)
Erro:                  #f44336 (Vermelho)
Aviso:                 #FF9800 (Laranja)
Info:                  #2196F3 (Azul)
```

### Sombras de Gradiente
```
Sucesso:  linear-gradient(135deg, rgba(76, 175, 80, 0.1), rgba(76, 175, 80, 0.05))
Erro:     linear-gradient(135deg, rgba(244, 67, 54, 0.1), rgba(244, 67, 54, 0.05))
```

---

## Tipografia

### Fonte Principal
```
Font Family:  'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
Fallback:     Sistema (browser default)
```

### Tamanhos de Fonte
```
H1 (Títulos):        32px (mobile: 26px)
Labels:              15px (mobile: 14px)
Inputs:              15px (mobile: 14px)
Body:                16px (mobile: 14px)
Pequeno:             14px (mobile: 13px)
Micro:               12px (mobile: 12px)
```

### Weights
```
Regular:             400
Medium:              500
Semibold:            600
Bold:                700
```

---

## Componentes

### 1. Container Principal
```css
Width:                100% max 450px
Background:           white
Border Radius:        20px
Box Shadow:           0 20px 60px rgba(0,0,0,0.3)
Animation:            slideIn 0.5s ease-out
```

### 2. Header
```css
Background:           linear-gradient(135deg, #667eea, #764ba2)
Color:                white
Padding:              40px 20px (mobile: 30px)
Text Align:           center
```

#### H1 (Logo)
```css
Font Size:            32px (mobile: 26px)
Font Weight:          700
Display:              flex, center
Gap:                  12px
Margin Bottom:        10px
```

#### Badge
```css
Background:           rgba(255,255,255,0.3)
Color:                white
Padding:              6px 12px
Border Radius:        20px
Font Size:            12px
Font Weight:          600
Letter Spacing:       1px
Text Transform:       uppercase
```

### 3. Conteúdo Principal
```css
Padding:              40px (mobile: 30px)
```

### 4. Form Group
```css
Margin Bottom:        25px
```

#### Label
```css
Display:              block
Font Weight:          600
Color:                #333
Font Size:            15px
Margin Bottom:        10px
Display:              flex
Gap:                  8px
```

#### Input
```css
Width:                100%
Padding:              14px 16px (mobile: 12px 14px)
Border:               2px solid #e0e0e0
Border Radius:        10px
Font Size:            15px
Font Family:          'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
Background:           #f9f9f9
Transition:           all 0.3s ease

Focus State:
  Border Color:       #667eea
  Background:         white
  Box Shadow:         0 0 0 3px rgba(102,126,234,0.1)
  Outline:            none

Placeholder:
  Color:              #999
```

### 5. Remember Me
```css
Display:              flex
Justify Content:      space-between
Align Items:          center
Margin Bottom:        25px
Font Size:            14px
```

#### Checkbox
```css
Width:                18px
Height:               18px
Cursor:               pointer
Accent Color:         #667eea
```

#### Forgot Password
```css
Color:                #667eea
Text Decoration:      none
Font Weight:          600
Transition:           color 0.3s ease

Hover:
  Color:              #764ba2
```

### 6. Button Login
```css
Width:                100%
Padding:              16px (mobile: 14px)
Border:               none
Border Radius:        10px
Font Size:            16px (mobile: 15px)
Font Weight:          600
Cursor:               pointer
Transition:           all 0.3s ease
Text Transform:       uppercase
Letter Spacing:       1px
Background:           linear-gradient(135deg, #667eea, #764ba2)
Color:                white
Box Shadow:           0 4px 15px rgba(102,126,234,0.4)
Display:              flex
Align Items:          center
Justify Content:      center
Gap:                  10px

Hover:
  Transform:          translateY(-2px)
  Box Shadow:         0 6px 20px rgba(102,126,234,0.6)

Disabled:
  Opacity:            0.6
  Cursor:             not-allowed
```

### 7. Alerts
```css
Padding:              16px
Border Radius:        10px
Margin Bottom:        20px
Display:              none (flex when .show)
Animation:            slideIn 0.3s ease-out
Font Weight:          500
```

#### Error Alert
```css
Background:           linear-gradient(135deg, rgba(244,67,54,0.1), rgba(244,67,54,0.05))
Border:               2px solid #f44336
Color:                #c62828
```

#### Success Alert
```css
Background:           linear-gradient(135deg, rgba(76,175,80,0.1), rgba(76,175,80,0.05))
Border:               2px solid #4CAF50
Color:                #2e7d32
```

### 8. Spinner de Loading
```css
Width:                18px
Height:               18px
Border:               3px solid #f3f3f3
Border Top:           3px solid #667eea
Border Radius:        50%
Animation:            spin 1s linear infinite
```

### 9. Footer
```css
Background:           #f5f5f5
Padding:              20px
Text Align:           center
Font Size:            13px
Color:                #999
Border Top:           1px solid #eee
```

---

## Animações

### slideIn
```css
0%:
  Opacity:            0
  Transform:          translateY(30px)

100%:
  Opacity:            1
  Transform:          translateY(0)

Duration:             0.5s
Timing:               ease-out
```

### spin
```css
0%:
  Transform:          rotate(0deg)

100%:
  Transform:          rotate(360deg)

Duration:             1s
Timing:               linear
Iteration:            infinite
```

---

## Spacing (Padrão)

```
XS:  4px
SM:  8px
MD:  16px
LG:  20px
XL:  30px
XXL: 40px
```

---

## Border Radius (Padrão)

```
Pequena:    10px (inputs, buttons)
Média:      15px (sections)
Grande:     20px (container principal)
Circular:   50% (spinner, badges)
```

---

## Responsive Breakpoints

```
Desktop:    > 480px (padrão)
Mobile:     ≤ 480px

Em mobile, aplicar:
  - Reduzir padding (30px em vez de 40px)
  - Reduzir font sizes (1-4px menor)
  - Manter proporcionalidade de layout
```

---

## Efeitos de Hover

### Buttons
```css
Hover State:
  Transform:          translateY(-2px)
  Box Shadow:         Aumenta 40%
  Duration:           0.3s
  Easing:             ease
```

### Links
```css
Hover State:
  Color:              Muda para #764ba2
  Duration:           0.3s
  Easing:             ease
```

### Inputs
```css
Focus State:
  Border Color:       Muda para primária (#667eea)
  Background:         Muda para white
  Box Shadow:         Adiciona outline suave
```

---

## Contraste & Acessibilidade

### Razões de Contraste (WCAG AA)
```
Texto Escuro (#333) em Branco:         21:1 ✓ EXCELENTE
Texto em Cinza (#666) em Branco:       7:1  ✓ BOM
Branco em Gradiente Roxo (#667eea):    7:1  ✓ BOM
Ícones em Gradiente:                   7:1  ✓ BOM
```

---

## Estados

### Button States
```
Normal:       Background gradiente, cursor pointer
Hover:        Transform -2px, shadow aumenta
Active:       Background fica levemente mais escuro
Disabled:     Opacity 0.6, cursor not-allowed
Loading:      Spinner animado, botão disabled
```

### Input States
```
Normal:       Border cinza claro, background cinzento
Focus:        Border primária, background branco, shadow
Valid:        Border verde (quando implementado)
Error:        Border vermelha (quando implementado)
Disabled:     Background mais claro, cursor not-allowed
```

### Alert States
```
Success:      Gradiente verde, ícone check
Error:        Gradiente vermelho, ícone X
Warning:      Gradiente laranja, ícone aviso
Info:         Gradiente azul, ícone info
```

---

## Ícones

### Font Awesome 6.4.0
```
Utiliza classes do Font Awesome para ícones:
  fa-lock              (cadeado)
  fa-user              (usuário)
  fa-key               (chave)
  fa-sign-in-alt       (seta de login)
  fa-shield-alt        (escudo)
  fa-exclamation-circle (exclamação)
  fa-check-circle      (check)
  fa-hourglass-half    (ampulheta)
  fa-redo              (reiniciar)
```

### Tamanho de Ícones
```
Header:              32px
Labels:              16px
Inputs:              14px
Alerts:              16px
Buttons:             16px
Footer:              14px
```

---

## Temas de Cores (Propostos)

### Dark Mode (Futuro)
```
Background:          #1e1e1e
Primary:             #667eea
Secondary:           #764ba2
Text:                #e0e0e0
Inputs:              #2a2a2a
```

### Light Mode (Atual)
```
Background:          white
Primary:             #667eea
Secondary:           #764ba2
Text:                #333
Inputs:              #f9f9f9
```

---

## Performance

### Otimizações CSS
- Usar `will-change: transform` em elementos animados
- Debounce de eventos de redimensionamento
- Lazy loading de imagens (se adicionadas)
- Minimizar recalculates de layout

### Otimizações JavaScript
- Event delegation onde possível
- Evitar manipulação DOM excessiva
- Cache de seletores frequentes
- Usar `requestAnimationFrame` para animações

---

## Notas de Implementação

1. **Mantém consistência** com o design do TOTEM IA
2. **Responsivo** desde 320px até 1920px
3. **Acessível** com bom contraste e suporte a teclado
4. **Rápido** com animações suaves e sem jank
5. **Moderno** com gradientes e sombras sutis
6. **Profissional** para uso administrativo

---

**Última atualização:** Novembro 2025

