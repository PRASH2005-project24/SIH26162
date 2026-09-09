import type { SIHCategory } from '@/types';

export const SIHCategoryIcons: Record<SIHCategory, string> = {
  'Industrial Fire': `
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <rect x="4" y="6" width="16" height="12" rx="2" fill="currentColor"/>
      <rect x="8" y="4" width="8" height="2" fill="currentColor"/>
      <rect x="6" y="2" width="12" height="2" rx="1" fill="currentColor"/>
    </svg>
  `,
  'Wildfire / Natural Fire': `
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2l3 9h6l-4 5 2 9-9-3-9 3 2-9-4-5h6z" fill="currentColor"/>
    </svg>
  `,
  'Agricultural Fire': `
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="currentColor"/>
      <path d="M8 8l4 4 4-4" stroke="white" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `,
  'Persistent Thermal Source': `
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0zm-9-3.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z" fill="currentColor"/>
    </svg>
  `,
  'Unknown / Other': `
    <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2l3 9h6l-4 5 2 9-9-3-9 3 2-9-4-5h6zM12 11.5l-1.5 2.5h3l-1.5-2.5z" fill="white"/>
    </svg>
  `
};