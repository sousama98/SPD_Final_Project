document.addEventListener('DOMContentLoaded', function () {
    console.log("Custom script.js loaded successfully!");

    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Other custom JavaScript code can go here
});
document.addEventListener('DOMContentLoaded', function () {
    var editUserModal = document.getElementById('editUserModal');
    editUserModal.addEventListener('show.bs.modal', function (event) {
        // Button that triggered the modal
        var button = event.relatedTarget;

        // Extract info from data-* attributes
        var userId = button.getAttribute('data-user-id');
        var userName = button.getAttribute('data-user-name');
        var userEmail = button.getAttribute('data-user-email');
        var userLocation = button.getAttribute('data-user-location');
        var userRole = button.getAttribute('data-user-role');
        var profileImage = button.getAttribute('data-profile-image');

        // Populate the form fields with the existing data
        document.getElementById('user_id').value = userId;
        document.getElementById('name').value = userName;
        document.getElementById('email').value = userEmail;
        document.getElementById('location').value = userLocation;
        document.getElementById('role').value = userRole;

        // If displaying the profile image, update it here
        if (profileImage) {
            var profileImgElement = document.getElementById('profile_image_display');
            profileImgElement.src = profileImage;  // Assuming profile_image is a URL path
        }
    });
});

    function toggleFields() {
        const listingType = document.getElementById('listing_type').value;
        const resourceFields = document.getElementById('resource_fields');
        const communityFields = document.getElementById('community_fields');

        // Toggle fields based on dropdown selection
        if (listingType === 'resource') {
            resourceFields.style.display = 'block';
            communityFields.style.display = 'none';
        } else if (listingType === 'community') {
            resourceFields.style.display = 'none';
            communityFields.style.display = 'block';
        } else {
            resourceFields.style.display = 'none';
            communityFields.style.display = 'none';
        }
    }
