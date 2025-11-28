# CSS Theme Variants - Professional Designs

Tento dokument popisuje tři nové profesionální varianty CSS pro rpiap webové rozhraní.

## 🎨 Přehled variant

### 1. **Modern Minimalist** (`styles-variant1-modern.css`)
**Inspirace:** Google Material Design

**Charakteristika:**
- Čisté, minimalistické rozhraní s důrazem na čitelnost
- Jemné stíny inspirované Material Design
- Zaoblené rohy pro moderní vzhled
- Vynikající typografie s anti-aliasingem

**Light Theme:**
- Primární barva: Google Blue (#1a73e8)
- Pozadí: Světle šedá (#fafafa)
- Důraz na bílý prostor a strukturu

**Dark Theme:**
- Tmavé pozadí (#121212, #1e1e1e)
- Jasné modré akcenty (#8ab4f8)
- Vysoký kontrast pro snadné čtení v noci

**Použití:**
```html
<link rel="stylesheet" href="/static/css/styles-variant1-modern.css">
```

---

### 2. **Vibrant Gradient** (`styles-variant2-vibrant.css`)
**Inspirace:** Moderní SaaS aplikace, Stripe, Vercel

**Charakteristika:**
- Výrazné barevné gradienty pro vizuální dopad
- Animované prvky (pulzující indikátory, hover efekty)
- Dynamické stíny s barevnými odstíny
- Energický a živý design

**Light Theme:**
- Gradient: Fialovo-modrý (#667eea → #764ba2)
- Pozadí: Jemně šedé (#f0f2f5)
- Barevné akcenty pro tlačítka a karty

**Dark Theme:**
- Velmi tmavé pozadí (#0f1419)
- Svítící gradienty pro kontrast
- Neonové efekty pro aktivní prvky

**Speciální funkce:**
- Animované tlačítka s ripple efektem
- Pulzující status indikátory
- Gradient text pro nadpisy
- Transformace při hover (scale, translateY)

**Použití:**
```html
<link rel="stylesheet" href="/static/css/styles-variant2-vibrant.css">
```

---

### 3. **Corporate Professional** (`styles-variant3-corporate.css`)
**Inspirace:** Enterprise aplikace, Tailwind UI

**Charakteristika:**
- Konzervativní, korporátní vzhled
- Důraz na profesionalitu a důvěryhodnost
- Temně modrá navigace
- Striktní typografie a hierarchie

**Light Theme:**
- Tmavě modrá navigace (#0a1f44)
- Primární modrá (#2563eb)
- Světle šedé pozadí (#f8f9fa)
- Klasický business design

**Dark Theme:**
- Slate šedé pozadí (#0f172a, #1e293b)
- Konzervativní barevné schéma
- Profesionální vzhled pro noční režim

**Speciální funkce:**
- Border-left akcenty u alerts
- Jemné animace pro profesionální dojem
- Klasické badge styly
- Přesná typografie s kerningem

**Použití:**
```html
<link rel="stylesheet" href="/static/css/styles-variant3-corporate.css">
```

---

## 🔄 Přepínání mezi variantami

Pro přepnutí mezi variantami stačí změnit odkaz na CSS soubor v hlavním template:

**Původní:**
```html
<link rel="stylesheet" href="/static/css/styles.css">
```

**Varianta 1 - Modern:**
```html
<link rel="stylesheet" href="/static/css/styles-variant1-modern.css">
```

**Varianta 2 - Vibrant:**
```html
<link rel="stylesheet" href="/static/css/styles-variant2-vibrant.css">
```

**Varianta 3 - Corporate:**
```html
<link rel="stylesheet" href="/static/css/styles-variant3-corporate.css">
```

---

## 🌓 Light/Dark Mode

Všechny varianty podporují přepínání mezi světlým a tmavým režimem pomocí atributu `data-theme`:

```html
<!-- Light mode (výchozí) -->
<html>

<!-- Dark mode -->
<html data-theme="dark">
```

**JavaScript pro přepínání:**
```javascript
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? '' : 'dark';
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Načtení uloženého motivu
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    document.documentElement.setAttribute('data-theme', savedTheme);
}
```

---

## 📊 Porovnání variant

| Vlastnost | Modern | Vibrant | Corporate |
|-----------|--------|---------|-----------|
| **Styl** | Minimalistický | Dynamický | Konzervativní |
| **Barvy** | Modré tóny | Gradienty | Tmavě modrá |
| **Animace** | Jemné | Výrazné | Střízlivé |
| **Použití** | Univerzální | Kreativní/Tech | Business/Enterprise |
| **Stíny** | Material Design | Barevné | Klasické |
| **Zaoblení** | Střední (8-12px) | Větší (10-16px) | Menší (4-6px) |

---

## 🎯 Doporučení použití

### Modern Minimalist
✅ **Ideální pro:**
- Univerzální použití
- Uživatelé očekávající Material Design
- Aplikace zaměřené na obsah a data
- Mobilní responzivní aplikace

### Vibrant Gradient
✅ **Ideální pro:**
- Mladší publikum
- Kreativní nebo tech startup atmosféra
- Dashboard s emphasis na vizuální atraktivitu
- Produkty vyžadující "wow" faktor

### Corporate Professional
✅ **Ideální pro:**
- Enterprise prostředí
- Korporátní klienti
- Formal business aplikace
- Konzervativnější publikum

---

## 🔧 Customizace

Všechny varianty používají CSS Custom Properties (proměnné), které lze snadno přizpůsobit:

```css
:root {
    --color-primary: #your-color;
    --bg-card: #your-background;
    --border-radius-md: 12px;
    /* ... další proměnné */
}
```

Klíčové proměnné k úpravě:
- `--color-primary` - hlavní barva brand
- `--bg-accent` - barva hlavičky
- `--border-radius-*` - zaoblení rohů
- `--spacing-*` - mezery mezi prvky
- `--shadow-*` - stíny

---

## 📱 Responsivita

Všechny tři varianty jsou plně responzivní s breakpointem na **768px**:

- **Desktop (>768px):** Sidebar viditelný, full layout
- **Mobile (≤768px):** Skrytý sidebar, hamburger menu, optimalizované rozložení

---

## ✨ Hlavní komponenty

Všechny varianty obsahují kompletní sadu UI komponent:

- ✅ Header s hamburger menu
- ✅ Sidebar s collapsible menu
- ✅ Tlačítka (primary, secondary, success, warning, danger)
- ✅ Formuláře (input, select, textarea, checkbox, radio, toggle)
- ✅ Karty (cards) a grid layout
- ✅ Alerts a notifikace (unified design s border-left akcenty)
- ✅ Status bary (successbar, errorbar, infobar) - alert styling
- ✅ Badges
- ✅ Progress bars
- ✅ Interface cards s status indikátory
- ✅ Speed test komponenty
- ✅ HTMX loading states

### Notification Bars

Status bary (successbar, errorbar, infobar) byly přepracovány na jednotný design:

- **Border-left design:** 4px barevný pruh vlevo (stejný jako alerts)
- **Barevné pozadí:** Jemné barevné pozadí podle typu (success, error, warning)
- **Mezera od headeru:** 12-16px padding pro oddělení od header/sidebar
- **Zaoblené rohy:** Moderní border-radius
- **Stíny:** Jemné stíny pro hloubku
- **Flexbox layout:** Správné zarovnání textu a close tlačítka
- **Konzistentní typografie:** Stejný font-weight a barvy jako alerts

---

## 🚀 Performance

Všechny varianty jsou optimalizovány pro:
- ⚡ Rychlé načítání (žádné externí závislosti)
- 🎨 Hardware akcelerované animace (transform, opacity)
- 📦 Minimální velikost souboru
- 🔄 Efektivní CSS transitions

---

## 📄 Licence

Tyto CSS varianty jsou součástí rpiap projektu a podléhají stejné licenci jako hlavní projekt.

---

## 👤 Autor & Datum

**Vytvořeno:** 24. listopadu 2025  
**Pro projekt:** rpiap (Raspberry Pi Access Point)

---

**Tip:** Pro nejlepší výsledky otestujte všechny tři varianty a vyberte tu, která nejlépe odpovídá vaší brand identitě a cílovému publiku.

