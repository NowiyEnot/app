$(document).ready(function() {
    $.ajax({
        type: 'GET',
        url: 'leaderboard', 
        success: function(data) {
            let currentUserGroupRank = data.current_user_rank; // Получаем место текущего пользователя в группе
            let userGroupRank = data.user_group_rank; // Получаем место текущего пользователя в потоке

            // Обновляем значения места пользователя в группе и в потоке
            $('.rating-conten-item:nth-child(1) p').text(currentUserGroupRank);
            $('.rating-conten-item:nth-child(2) p').text(userGroupRank);

            function createLeaderItem(leader, index) {
                let leaderItem = $('<div class="leader-item">' +
                    '<div class="leader-info">' +
                    '<div class="leader-number">' + (index + 1) + '</div>' +
                    '<div class="leader-name">' + leader.full_name + '</div>' +
                    '</div>' +
                    '<div class="leader-score">' + leader.total_score + '</div>' +
                    '</div>');

                if (leader.rank === currentUserGroupRank) {
                    leaderItem.addClass('current-user'); 
                }
                return leaderItem;
            }

            function updateLeaderboard(leaders) {
                $('#leaderboard-body').empty();
                $.each(leaders, function(index, leader) {
                    let leaderItem = createLeaderItem(leader, index);
                    $('#leaderboard-body').append(leaderItem);
                });
            }

            function showGroup() {
                $('.stream-button').removeClass('active');
                $('.group-button').addClass('active');
                updateLeaderboard(data.user_group_leaders);
            }

            function showStream() {
                $('.group-button').removeClass('active');
                $('.stream-button').addClass('active');
                updateLeaderboard(data.leaders);
                // Выделяем пользователя в потоке по его номеру в группе
                $('.leader-item').removeClass('stream-rank-user'); // Удаляем выделение у предыдущего пользователя
                $('.leader-item:nth-child(' + currentUserGroupRank + ')').addClass('stream-rank-user'); // Выделяем пользователя, чей номер соответствует рангу в группе
            }

            showGroup();

            $('.group-button').click(showGroup);
            $('.stream-button').click(showStream);
        },
        error: function(xhr, status, error) {
            console.error("Error fetching leaderboard:", error);
        }
    });
});
