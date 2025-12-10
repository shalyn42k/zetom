/*
# === FILE SUMMARY ===
# Purpose: Provide a reusable password input component with show/hide toggle behaviour.
# Responsible for: Enhancing native password inputs with a toggleable visibility icon and accessible markup.
# Connected to: All templates loading this script (e.g., admin login, admin panel forms).
# Important classes/functions: PasswordInput class, initPasswordInputs helper.
# Notes: Auto-initialises on DOMContentLoaded and safely ignores inputs already processed.
# =====================================
*/
(function () {
    class PasswordInput {
        constructor(input) {
            if (!input || input.dataset.passwordInputInitialized === 'true') {
                return;
            }

            this.input = input;
            this.isVisible = false;
            this.input.dataset.passwordInputInitialized = 'true';
            this.build();
        }

        build() {
            const wrapper = document.createElement('div');
            wrapper.classList.add('password-input');

            const toggleButton = document.createElement('button');
            toggleButton.type = 'button';
            toggleButton.className = 'password-input__toggle';
            toggleButton.innerHTML = this.renderIcons();
            toggleButton.setAttribute('aria-label', 'Show password');
            toggleButton.setAttribute('aria-pressed', 'false');

            this.input.classList.add('password-input__field');
            this.input.setAttribute('autocomplete', this.input.getAttribute('autocomplete') || 'current-password');

            const parent = this.input.parentElement;
            if (parent) {
                parent.insertBefore(wrapper, this.input);
            }
            wrapper.appendChild(this.input);
            wrapper.appendChild(toggleButton);

            toggleButton.addEventListener('click', () => this.toggleVisibility());

            this.toggleButton = toggleButton;
            this.updateToggleState();
        }

        toggleVisibility() {
            this.isVisible = !this.isVisible;
            this.input.setAttribute('type', this.isVisible ? 'text' : 'password');
            this.updateToggleState();
        }

        updateToggleState() {
            this.toggleButton.classList.toggle('is-visible', this.isVisible);
            this.toggleButton.setAttribute('aria-label', this.isVisible ? 'Hide password' : 'Show password');
            this.toggleButton.setAttribute('aria-pressed', this.isVisible ? 'true' : 'false');
        }

        renderIcons() {
            return `
                <svg class="password-input__icon password-input__icon--show" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M12 5C7 5 2.73 8.11 1 12c1.73 3.89 6 7 11 7s9.27-3.11 11-7c-1.73-3.89-6-7-11-7zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10zm0-2a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"></path>
                </svg>
                <svg class="password-input__icon password-input__icon--hide" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path d="M3.27 2 2 3.27l3.11 3.11A11.7 11.7 0 0 0 1 12c1.73 3.89 6 7 11 7 1.99 0 3.88-.44 5.61-1.23L20.73 22 22 20.73 3.27 2zM12 17c-3.51 0-6.79-2.06-8.48-5 1.02-1.78 2.56-3.15 4.37-4.02l1.53 1.53A3 3 0 0 0 12 15c.48 0 .94-.11 1.35-.29l1.55 1.55A9.2 9.2 0 0 1 12 17zm0-10c3.5 0 6.78 2.06 8.48 5-.69 1.2-1.6 2.21-2.66 3.01l-1.45-1.45a3 3 0 0 0-3.93-3.93L10 7.52c.64-.34 1.32-.52 2-.52z"></path>
                </svg>
            `;
        }
    }

    const initPasswordInputs = (root = document) => {
        const passwordFields = Array.from(root.querySelectorAll('input[type="password"]'));
        passwordFields.forEach((input) => new PasswordInput(input));
    };

    window.PasswordInput = PasswordInput;
    window.initPasswordInputs = initPasswordInputs;

    document.addEventListener('DOMContentLoaded', () => {
        initPasswordInputs();
    });
})();
