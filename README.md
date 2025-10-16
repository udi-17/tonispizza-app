# Golden-Bis Food Ordering Kiosk

A modern React-based food ordering kiosk application with Hebrew language support.

## Features

- 🍔 **Menu Categories**: Burgers, Sides, and Drinks
- 🛒 **Shopping Cart**: Add items and view total
- 🎨 **Modern UI**: Built with Tailwind CSS
- 🌐 **RTL Support**: Full Hebrew language support
- 📱 **Responsive Design**: Works on different screen sizes
- ⚡ **Fast Development**: Powered by Vite

## Menu Items

### Burgers
- Golden Classic - 45₪
- Double Deluxe - 55₪
- Vegan King - 48₪

### Sides
- צ'יפס קלאסי (Classic Fries) - 15₪
- טבעות בצל (Onion Rings) - 18₪

### Drinks
- קולה (Cola) - 10₪
- מים (Water) - 8₪

## Getting Started

### Prerequisites
- Node.js (version 16 or higher)
- npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:3002`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
├── public/
│   └── img/           # Menu item images (SVG)
├── src/
│   ├── App.jsx        # Main application component
│   ├── App.css        # Custom styles
│   ├── index.css      # Global styles
│   └── main.jsx       # Application entry point
├── index.html         # HTML template
├── package.json       # Dependencies and scripts
├── tailwind.config.js # Tailwind CSS configuration
└── vite.config.js     # Vite configuration
```

## Technologies Used

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **PostCSS** - CSS processing
- **ESLint** - Code linting

## Customization

### Adding New Menu Items

Edit the `menu` object in `src/App.jsx`:

```javascript
const menu = {
  burgers: [
    { id: 1, name: "New Burger", price: 50, image: "/img/new-burger.svg" },
    // ... other items
  ],
  // ... other categories
};
```

### Styling

The application uses Tailwind CSS. You can customize styles in:
- `src/App.css` - Custom component styles
- `src/index.css` - Global styles
- `tailwind.config.js` - Tailwind configuration

## License

This project is open source and available under the MIT License.