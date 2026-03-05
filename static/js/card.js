function createMemberHTML(member, isArticle = false) {
    if (isArticle) {
        return `
            <div class="flex items-center bg-black text-white rounded-xl pl-3 pr-1 py-1 shadow-sm member-badge" data-member="${member}">
                <button type="button" class="font-bold text-lg mr-2 hover:text-gray-300 transition"
                    onclick="onMemberClick(event, '${member}')">
                    ${member}
                </button>
                <button type="button" data-member="${member}"
                    class="w-7 h-7 flex items-center justify-center bg-gray-600 rounded-lg hover:bg-gray-500 transition"
                    onclick="onRemoveMemberClick(event, '${member}')">
                    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24"
                        stroke="currentColor" stroke-width="3">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `;
    }
    return `<span onclick="onMemberClick(event, '${member}')" class="text-xl font-medium text-gray-400 cursor-pointer mr-1">@${member}</span>`;
}

function createCardHTML(card) {
    const diff = new Date(card.card_duedate) - new Date()
    const opacityClass = diff <= 0 ? 'opacity-50 pointer-events-none' : ''
    const membersHTML = (card.card_members || [])
        .slice(1) // 작성자 제외
        .map(m => createMemberHTML(m, false))
        .join('')

    return `
        <div onclick="onCardClick('${card._id}')" class="flex flex-col gap-3 p-4 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${opacityClass}">
            <div class="flex items-center justify-between">
                <span class="font-semibold text-xl font-medium text-gray-400 countdown" data-duedate="${card.card_duedate}">--:--:--</span>
                <span class="text-l text-gray-400">${card.card_duedate}</span>
            </div>

            <h3 class="text-2xl font-semibold text-gray-900 truncate">${card.card_title}</h3>

            <div class="flex items-center justify-end">
                <div class="flex items-center gap-1">
                    <img onclick="onIconClick(event, '${card.card_url}')" src="${card.card_type}" class="w-12 h-12 rounded-md object-cover cursor-pointer hover:opacity-80 transition" />
                </div>
                <span class="px-3 text-2xl font-semibold text-gray-800 pointer-events-none">${Number(card.card_price).toLocaleString()}원</span>
            </div>

            <div class="flex items-center justify-between mt-2">
                <div class="truncate flex-1 min-w-0 mr-4">
                    ${membersHTML}
                </div>
                <div class="flex items-center text-gray-400 font-bold text-lg gap-1 shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-6 h-6">
                        <path fill-rule="evenodd"
                        d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z"
                        clip-rule="evenodd" />
                    </svg>
                <span>${card.card_members ? card.card_members.length : 0}</span>
                </div>
            </div>
        </div>
    `
}

function renderCards(cards) {
    const grid = document.getElementById('cardGrid')
    grid.innerHTML = ''
    cards.forEach(card => grid.innerHTML += createCardHTML(card))
}

function startCountdowns() {
    function update() {
        document.querySelectorAll('.countdown').forEach(el => {
            const diff = new Date(el.dataset.duedate) - new Date()
            if (diff <= 600000) {
                el.textContent = diff <= 0 ? '종료' : '마감임박'
                return
            }
            const h = Math.floor(diff / 3600000)
            const m = Math.floor((diff % 3600000) / 60000)
            const s = Math.floor((diff % 60000) / 1000)
            el.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
        })
    }
    update()
    setInterval(update, 1000)
}

function onCardClick(cardId) {
    window.location.href = `/food/${cardId}`
}

function onIconClick(event, url) {
    event.stopPropagation()
    if (url && url !== 'None' && url.trim() !== '') {
        window.open(url, '_blank')
    }
}

async function onMemberClick(event, nickname) {
    event.stopPropagation()
    try {
        const response = await fetch(`/food/profile?nickname=${encodeURIComponent(nickname)}`)
        const data = await response.json()
        if (data.result === 'success' && data.slack_url) {
            window.open(data.slack_url, '_blank')
        } else {
            alert(data.message || '사용자를 찾을 수 없습니다.')
        }
    } catch (error) {
        alert('서버 연결에 실패했습니다.')
    }
}
