```typescript
/* GlobalStyles.ts */

// ...existing styles...

body.flash-mode {
  transition: background-color 0.5s ease;
  background-color: rgba(255, 255, 255, 0.8); /* Light flash */
}

body.light-mode.flash-mode {
  background-color: rgba(0, 0, 0, 0.8); /* Dark flash */
}

/* ...existing styles... */
```