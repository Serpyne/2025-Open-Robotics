const clickDelay = 100;
const interactiveContainer = document.getElementById("interactive-container");
const BTDropdownContainer = document.getElementById('behaviour-tree-container')
const BTDropdownHeader = document.getElementById('bt-dropdownHeader');
const BTDropdownContent = document.getElementById('bt-dropdown-content');
const BTDropdownIcon = document.getElementById('bt-dropdown-icon');
const BTTextarea = document.getElementById('behaviour-tree-display');

BTDropdownHeader.addEventListener('click', () => {
    BTDropdownHeader.classList.toggle('active');
    interactiveContainer.classList.toggle('open');
    BTDropdownContent.classList.toggle('open');
    BTDropdownIcon.classList.toggle('rotate');
    
    if (BTDropdownContent.classList.contains('open')) {
        setTimeout(() => {
            BTTextarea.focus();
        }, clickDelay);
    }
});

const FDDropdownContainer = document.getElementById('field-display-container')
const FDDropdownHeader = document.getElementById('fd-dropdownHeader');
const FDDropdownContent = document.getElementById('fd-dropdown-content');
const FDDropdownIcon = document.getElementById('fd-dropdown-icon');
const FDTextarea = document.getElementById('field-display');

FDDropdownHeader.addEventListener('click', () => {
    FDDropdownHeader.classList.toggle('active');
    FDDropdownContent.classList.toggle('open');
    interactiveContainer.classList.toggle('open');
    FDDropdownIcon.classList.toggle('rotate');
    
    if (FDDropdownContent.classList.contains('open')) {
        setTimeout(() => {
            FDTextarea.focus();
        }, clickDelay);
    }
});
