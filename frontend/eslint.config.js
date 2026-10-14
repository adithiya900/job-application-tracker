import js from '@eslint/js';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';

export default [
  {
    ignores: ['dist'],
  },

  js.configs.recommended,

  {
    files: ['**/*.{js,jsx}'],

    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        URLSearchParams: 'readonly',
        Blob: 'readonly',
        AbortController: 'readonly',
        TextDecoder: 'readonly',
        CustomEvent: 'readonly',
        confirm: 'readonly',
        prompt: 'readonly',
        Event: 'readonly',
        URL: 'readonly',
        FormData: 'readonly',
        File: 'readonly',
        FileList: 'readonly',
        btoa: 'readonly',
        atob: 'readonly',
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },

    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },

    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': 'warn',
      // Data-fetching patterns (calling async handlers in useEffect) are standard
      // React patterns; the set-state-in-effect rule is too aggressive for them.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
];
