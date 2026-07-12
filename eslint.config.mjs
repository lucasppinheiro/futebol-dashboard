import js from '@eslint/js';
import globals from 'globals';
import prettier from 'eslint-config-prettier';

export default [
    { ignores: ['dist/', 'node_modules/', 'coverage/'] },
    js.configs.recommended,
    prettier,
    {
        files: ['static/js/**/*.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'script',
            globals: {
                ...globals.browser,
                Chart: 'readonly',
                timeData: 'readonly',
                todosClassificacao: 'readonly',
                dadosClassificacao: 'readonly',
                dadosArtilharia: 'readonly'
            }
        }
    },
    {
        files: ['tests/js/**/*.js'],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: 'commonjs',
            globals: { ...globals.node, ...globals.jest }
        }
    }
];
