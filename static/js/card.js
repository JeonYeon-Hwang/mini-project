function createCardHTML(card) {
    const diff = new Date(card.card_duedate) - new Date()
    const opacityClass = diff <= 0 ? 'opacity-50 pointer-events-none' : ''
    const membersHTML = (card.card_members || [])
        .map(m => `<span onclick="onMemberClick(event, '${m}')" class="text-xl font-medium text-gray-400 cursor-pointer">@${m}</span>`)
        .join('')

    return `
        <div onclick="onCardClick('${card._id}')" class="flex flex-col gap-3 p-4 bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow cursor-pointer ${opacityClass}">
            <div class="flex items-center justify-between">
                <span class="font-semibold text-xl font-medium text-gray-400 countdown" data-duedate="${card.card_duedate}">--:--:--</span>
                <span class="text-l text-gray-400">${card.card_duedate}</span>
            </div>

            <h3 class="text-2xl font-semibold text-gray-900 truncate">${card.card_title}</h3>

            <div onclick="onIconClick(event, '${card.card_url}')" class="flex items-center justify-end cursor-pointer">
                <div class="flex items-center gap-1">
                    <img src="${card.card_type}" class="w-12 h-12 rounded-md object-cover" />
                </div>
                <span class="px-3 text-2xl font-semibold text-gray-800">${Number(card.card_price).toLocaleString()}원</span>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex flex-wrap gap-1">
                    ${membersHTML}
                </div>
                <div class="flex items-center gap-1 text-xl text-gray-400">
                    <img src="https://picsum.photos/64/64" class="w-8 h-8 rounded-md object-cover" />
                    <span>${(card.card_members || []).length}</span>
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
    console.log("메뉴 링크 이동");
}

async function onMemberClick(event, nickname) {
    event.stopPropagation()
    console.log(`멤버 ${nickname} 클릭`)
}
