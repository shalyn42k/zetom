(function () {
    const ready = (callback) => {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    };

    ready(() => {
        const form = document.querySelector('[data-contact-form]');
        if (form) {
            const botCheckbox = form.querySelector('[data-bot-check]');
            const submitButton = form.querySelector('[data-form-submit]');
            const botError = form.querySelector('[data-bot-error]');
            const requiredMessage = form.dataset.botRequiredMessage || '';

            const showBotError = (message) => {
                if (!botError) {
                    return;
                }
                botError.textContent = message;
                botError.hidden = !message;
            };

            const updateSubmitState = () => {
                if (!submitButton) {
                    return;
                }
                const isChecked = botCheckbox ? botCheckbox.checked : true;
                submitButton.disabled = !isChecked;
            };

            updateSubmitState();

            if (botCheckbox) {
                botCheckbox.addEventListener('change', () => {
                    updateSubmitState();
                    if (botCheckbox.checked) {
                        showBotError('');
                    }
                });
            }

            form.addEventListener('submit', (event) => {
                if (botCheckbox && !botCheckbox.checked) {
                    event.preventDefault();
                    updateSubmitState();
                    if (requiredMessage) {
                        showBotError(requiredMessage);
                    }
                }
            });
        }

        const successModal = document.querySelector('[data-success-modal]');
        if (successModal) {
            const closeElements = successModal.querySelectorAll('[data-success-close]');
            const closeModal = () => {
                successModal.classList.remove('is-visible');
                successModal.setAttribute('aria-hidden', 'true');
            };

            successModal.classList.add('is-visible');
            successModal.setAttribute('aria-hidden', 'false');

            closeElements.forEach((element) => {
                element.addEventListener('click', closeModal);
            });

            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && successModal.classList.contains('is-visible')) {
                    closeModal();
                }
            });
        }
    });
})();
