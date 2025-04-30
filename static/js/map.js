const apiKeySuggest = 'ce8efa73-9786-4290-9c44-961d4ea15f04';
const apiKeyCoder = 'ce095acd-05a3-4919-9cf4-7e64c641af28';
const apiKey2GIS = '40908dcf-36e0-4831-a99d-7face9aadadd';
let map, placemark, targetInputId;
let coordsA = null;
let coordsB = null;

// Функция для отображения подсказок
function fetchSuggestions(inputId, suggestionsId) {
    const input = document.getElementById(inputId);
    const suggestionsContainer = document.getElementById(suggestionsId);

    input.addEventListener('input', function () {
        const query = input.value;
        if (query.length < 3) {
            suggestionsContainer.innerHTML = '';
            return;
        }

        fetch(`https://suggest-maps.yandex.ru/v1/suggest?apikey=${apiKeySuggest}&text=${query}&results=5`)
            .then(response => response.json())
            .then(data => {
                suggestionsContainer.innerHTML = '';
                const results = data.results;

                if (results) {
                    results.forEach(item => {
                        const suggestionText = item.title.text;
                        const highlightedText = highlightText(suggestionText, item.title.hl);

                        const suggestion = document.createElement('div');
                        suggestion.classList.add('suggestion');
                        suggestion.innerHTML = highlightedText;
                        suggestion.addEventListener('click', () => {
                            input.value = suggestionText;
                            suggestionsContainer.innerHTML = '';

                            fetch(`https://geocode-maps.yandex.ru/v1/?apikey=${apiKeyCoder}&geocode=${suggestionText}&format=json&lang=ru_RU`)
                                .then(response => response.json())
                                .then(data => {
                                    const featureMember = data.response.GeoObjectCollection.featureMember;

                                    if (featureMember && featureMember.length > 0) {
                                        const coordinates = featureMember[0].GeoObject.Point.pos;

                                        if (inputId === pointA)
                                            coordsA = [parseFloat(coordinates.split(' ')[0]), parseFloat(coordinates.split(' ')[1])];
                                        else
                                            coordsB = [parseFloat(coordinates.split(' ')[1]), parseFloat(coordinates.split(' ')[0])];
                                    }
                                })

                            calculatePrice();  // Перерасчет цены при выборе адреса
                        });
                        suggestionsContainer.appendChild(suggestion);
                    });
                }
            })
            .catch(error => console.error('Error fetching Yandex data:', error));
    });
}

// Функция для подсветки части текста в подсказках
function highlightText(text, hlArray) {
    if (!hlArray || hlArray.length === 0) return text;

    let highlightedText = text;
    hlArray.reverse().forEach(hl => {
        const start = hl.begin;
        const end = hl.end;
        const highlightedPart = `<span class="highlight">${text.substring(start, end)}</span>`;
        highlightedText = highlightedText.slice(0, start) + highlightedPart + highlightedText.slice(end);
    });
    return highlightedText;
}

// Функция для вычисления стоимости поездки с обращением к API 2ГИС
function calculatePrice() {
    const pointA = document.getElementById('pointA').value;
    const pointB = document.getElementById('pointB').value;



    if (pointA && pointB)
        if (coordsA && coordsB)
            getRouteFrom2GIS(coordsA[0], coordsA[1], coordsB[0], coordsB[1]);

}

// Функция для запроса маршрута через API 2ГИС
function getRouteFrom2GIS(lat1, lon1, lat2, lon2) {
    const url = 'https://routing.api.2gis.com/get_dist_matrix?key=' + apiKey2GIS + '&version=2.0';

    const data = {
        points: [
            { lat: lat1, lon: lon1 },
            { lat: lat2, lon: lon2 }
        ],
        sources: [0],
        targets: [1],
        type: "jam"
    };

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => {
        if (data.routes && data.routes.length > 0) {
            const route = data.routes[0];
            const distance = route.distance;
            const time = route.duration;
            updatePrice(distance / 1000, time / 60);
        } else {
            console.error("Маршрут не найден");
        }
    })
    .catch(error => console.error("Ошибка при запросе маршрута:", error));
}

// Функция для обновления стоимости поездки
function updatePrice(distance, time) {
    const carType = document.getElementById("carType").value;
    let price;

    const distanceInKm = distance / 1000;

    switch (carType) {
        case 'econom':
            price = 150 + Math.max(distanceInKm * 10, time * 3);
            break;
        case 'comfort':
            price = 210 + Math.max(distanceInKm * 12, time * 4);
            break;
        case 'business':
            price = 350 + Math.max(distanceInKm * 15, time * 5);
            break;
        case 'minivan':
            price = 240 + Math.max(distanceInKm * 12, time * 4);
            break;
    }

    document.getElementById("price").innerText = price.toFixed(2);
    document.getElementById("priceCalculation").style.display = 'block';
}

// Функция для получения геолокации пользователя
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            fetch(`https://geocode-maps.yandex.ru/v1/?apikey=${apiKeyCoder}&geocode=${position.coords.longitude},${position.coords.latitude}&format=json&lang=ru_RU`)
                .then(response => response.json())
                .then(data => {
                    const featureMember = data.response.GeoObjectCollection.featureMember;

                    if (featureMember && featureMember.length > 0) {
                        const address = featureMember[0].GeoObject.metaDataProperty.GeocoderMetaData.text;
                        document.getElementById('pointA').value = address;
                        coordsA = [position.coords.latitude, position.coords.longitude];  // Сохраняем координаты для Пункта А
                    } else {
                        console.error("Адрес не найден.");
                    }
                })
                .catch(error => {
                    console.error('Error fetching geocoding data:', error);
                    alert("Ошибка при получении данных с геокодера.");
                });

            fetchSuggestions('pointA', 'suggestionsA');
            fetchSuggestions('pointB', 'suggestionsB');
        }, function(error) {
            alert("Не удалось получить геолокацию. Используйте поиск по адресу.");
        });
    } else {
        alert("Геолокация не поддерживается вашим браузером.");
    }
}

// Инициализация карты
function initMap() {
    ymaps3.ready.then(() => {
        map = new ymaps3.YMap(document.getElementById('map'), {
            location: {
                center: [55.7558, 37.6173],  // Начальные координаты (Москва)
                zoom: 10
            }
        });

        placemark = new ymaps3.YPlacemark([55.7558, 37.6173], {
            balloonContent: "Выберите точку на карте"
        });

        map.geoObjects.add(placemark);

        map.events.add('click', (e) => {
            const coords = e.get('coords');
            placemark.geometry.setCoordinates(coords);  // Перемещаем метку
            fetchAddressFromCoords(coords);  // Получаем адрес по координатам
        });
    });
}

// Получение адреса по координатам с помощью геокодера Яндекс
function fetchAddressFromCoords(coords) {
    fetch(`/get_address?lat=${coords[1]}&lon=${coords[0]}`)
        .then(res => res.json())
        .then(data => {
            if (data.address) {
                document.getElementById(targetInputId).value = data.address;
                if (targetInputId === 'pointA') {
                    coordsA = [coords[1], coords[0]];  // Сохраняем координаты для Пункта A
                } else if (targetInputId === 'pointB') {
                    coordsB = [coords[1], coords[0]];  // Сохраняем координаты для Пункта B
                }
                if (coordsA && coordsB) {
                    getRouteFrom2GIS(coordsA[0], coordsA[1], coordsB[0], coordsB[1]);  // Запрос маршрута при выборе обеих точек
                }
            }
        })
        .catch(error => console.error('Error fetching address:', error));
}

document.getElementById("selectPointA").addEventListener('click', function () {
    targetInputId = 'pointA';
    document.getElementById('map').style.display = 'block';
    initMap();
});

document.getElementById("selectPointB").addEventListener('click', function () {
    targetInputId = 'pointB';
    document.getElementById('map').style.display = 'block';
    initMap();
});

document.getElementById('carType').addEventListener('change', function () {
    calculatePrice();
});

getUserLocation();
