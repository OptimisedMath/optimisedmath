import streamlit.components.v1 as components


def inject_enter_hack(target_button_text=None):
    """DRY Helper: Injects JS to click a specific button ONLY on a fresh Enter press."""
    if target_button_text is None or target_button_text == "NONE":
        components.html(
            """
            <script>
            const doc = window.parent.document;
            if (doc.customKeyDown) doc.removeEventListener('keydown', doc.customKeyDown, true);
            if (doc.customKeyUp) doc.removeEventListener('keyup', doc.customKeyUp, true);
            </script>
            """,
            height=0,
            width=0,
        )
    else:
        components.html(
            f"""
            <script>
            const doc = window.parent.document;
            
            // 1. Clear old listeners to prevent double-firing
            if (doc.customKeyDown) doc.removeEventListener('keydown', doc.customKeyDown, true);
            if (doc.customKeyUp) doc.removeEventListener('keyup', doc.customKeyUp, true);
            
            let freshPress = false;
            
            // 2. Track when the key is explicitly pressed DOWN on this new screen
            doc.customKeyDown = function(e) {{
                if (e.key === 'Enter' && !e.repeat) {{
                    freshPress = true; 
                }}
            }};
            
            // 3. Only click the button if the key goes UP after being pressed DOWN
            doc.customKeyUp = function(e) {{
                if (e.key === 'Enter' && freshPress) {{
                    const allButtons = Array.from(doc.querySelectorAll('button'));
                    const targetBtn = allButtons.find(b => b.innerText.includes('{target_button_text}'));
                    if (targetBtn) targetBtn.click();
                    freshPress = false; // Reset for safety
                }}
            }};
            
            doc.addEventListener('keydown', doc.customKeyDown, true);
            doc.addEventListener('keyup', doc.customKeyUp, true);
            </script>
            """,
            height=0,
            width=0,
        )


def inject_decimal_keyboard():
    """Forces mobile devices to open the Number/Decimal pad instead of the Alphabet."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        // Find the Streamlit text input box
        const inputNodes = doc.querySelectorAll('input[type="text"]');
        
        inputNodes.forEach(input => {
            // Only target inputs that are actually for math answers
            if (!input.hasAttribute('data-keyboard-hacked')) {
                input.setAttribute('inputmode', 'decimal');
                // pattern="\d*" is an iOS specific hack to trigger the tall numpad
                input.setAttribute('pattern', '[0-9]*'); 
                input.setAttribute('data-keyboard-hacked', 'true');
            }
        });
        </script>
        """,
        height=0,
        width=0,
    )
