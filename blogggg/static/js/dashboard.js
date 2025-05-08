// Handle skill tags
const skillInput = document.getElementById('skill-input');
const addSkillBtn = document.querySelector('.add-skill-btn');
const skillTags = document.querySelector('.skill-tags');

addSkillBtn.addEventListener('click', () => {
    const skill = skillInput.value.trim();
    if (skill) {
        const tag = document.createElement('div');
        tag.className = 'skill-tag';
        tag.innerHTML = `
            ${skill}
            <i class="fas fa-times" onclick="this.parentElement.remove()"></i>
        `;
        skillTags.appendChild(tag);
        skillInput.value = '';
    }
});

// Handle other interests
const otherInterestInput = document.getElementById('other-interest-input');
const addOtherBtn = document.querySelector('.add-other-btn');
const otherInterestsTags = document.querySelector('.other-interests-tags');
const otherCheckbox = document.getElementById('other');

addOtherBtn.addEventListener('click', () => {
    const interest = otherInterestInput.value.trim();
    if (interest) {
        const tag = document.createElement('div');
        tag.className = 'interest-tag';
        tag.innerHTML = `
            ${interest}
            <i class="fas fa-times" onclick="removeOtherInterest(this)"></i>
        `;
        otherInterestsTags.appendChild(tag);
        otherInterestInput.value = '';
    }
});

function removeOtherInterest(element) {
    element.parentElement.remove();
    if (otherInterestsTags.children.length === 0 && !otherInterestInput.value) {
        otherCheckbox.checked = false;
    }
}

// Handle form submission
document.querySelector('.profile-form').addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Collect all interests including custom ones
    const selectedInterests = [];
    document.querySelectorAll('input[name="interests[]"]:checked').forEach(checkbox => {
        if (checkbox.value !== 'other') {
            selectedInterests.push(checkbox.value);
        }
    });
    
    document.querySelectorAll('.other-interests-tags .interest-tag').forEach(tag => {
        selectedInterests.push(tag.textContent.trim());
    });

//     // Add your form submission logic here
    console.log('Selected interests:', selectedInterests);
    // alert('Profile updated successfully!');
});