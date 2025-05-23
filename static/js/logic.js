const apiKeySuggest = 'ce8efa73-9786-4290-9c44-961d4ea15f04';
const apiKeyCoder = 'ce095acd-05a3-4919-9cf4-7e64c641af28';
const apiKey2GIS = '40908dcf-36e0-4831-a99d-7face9aadadd';

let targetInputId;
let coordsA = null;
let coordsB = null;
let mapFlag = false;

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
function getRouteFrom2GIS(lon1, lat1, lon2, lat2) {
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
    const carType = document.getElementById("carTypeValue").value;
    let price;

    const distanceInKm = distance / 1000;

    switch (carType) {
        case 'econom':
            price = 250 + Math.max(distanceInKm * 15, time * 5);
            break;
        case 'comfort':
            price = 350 + Math.max(distanceInKm * 17, time * 6);
            break;
        case 'business':
            price = 550 + Math.max(distanceInKm * 25, time * 10);
            break;
        case 'minivan':
            price = 350 + Math.max(distanceInKm * 18, time * 7);
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
                        coordsA = [position.coords.longitude, position.coords.latitude];
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
async function initMap() {
    if (!mapFlag) {
        mapFlag = true;

        await ymaps3.ready;

        const {
            YMap,
            YMapDefaultSchemeLayer,
            YMapControls,
            YMapDefaultFeaturesLayer,
            YMapMarker,
            YMapListener
        } = ymaps3;

        const {
            YMapZoomControl,
            YMapGeolocationControl
        } = await ymaps3.import('@yandex/ymaps3-controls@0.0.1');

        const LOCATION = {center: coordsA, zoom: 17};

        let map = new YMap(document.getElementById('map'), {location: LOCATION});

        map.addChild(new YMapDefaultSchemeLayer());
        map.addChild(new YMapDefaultFeaturesLayer({zIndex: 1800}))


        map.addChild(new YMapControls({position: 'right'})
            .addChild(new YMapZoomControl({}))
        );

        map.addChild(new YMapControls({position: 'top right'})
            .addChild(new YMapGeolocationControl({}))
        );

        let flag = false;

        const clickCallback = (object, event) => {
            if (!flag) {
                const coordinates = event.coordinates;

                if (targetInputId === "pointA") {
                    coordsA = coordinates;
                } else {
                    coordsB = coordinates;
                }

                const markerElement = document.createElement('div');
                markerElement.className = 'marker-class';
                markerElement.innerHTML = '<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAAsTAAALEwEAmpwYAAABuklEQVR4nO2WsUoDQRRFp9FK/IWwo6ImWOUXBGuFzKgYsIqFnZUSWyuTaLBJsLNR8AvUwsKsJDGd8R920SaJVi5cmVl0o3FjIsjMyhx47JT3vvtm5xFi+GdgeSIBbh2AWU0w+uyXPBeQmowTXUEqPgpGj8CpB04RUh6YVUQmOUK0E8/plRS5OgVkF4HyDnCW879fjTB6qZUJ+J0H1ueA413gvBhUafv7NJh1SPSZeerJzr+LP9kDthaAtemwUQK49Qoem1Wtn4hOSkHZpUB8Ot5H+KdRyqvWT8CtBylGzLowIDo/iHg/hXsdDHSkmNOcb6Dv2PQYaOtgoP2RQNiFDR0hq6XDHWgOJVq7EWK08GsDjO6r1k/EevDD6xv+G12JzRAdkOvB8N0vEF0Qa4FcDwYXf6HVKhGYEI+aeGH7jI24M7qJ77kTjOZfNufhpROyxBmc5rRYHQbFrrvoLhI1bGNAMSYB1ZgEVGMSUI1JQDUmAdWYBFRjElCNSUA1JgHVmARUY9edRpCC0yBR4/bO2egykCFR47rpjlXqTsuuOZ1q9WmcRJFKzS1Xam6JRJWb6mNSlGodBvKHvAEmVo/4wCwVdgAAAABJRU5ErkJggg==" alt="map-pin">';

                const marker = new YMapMarker({
                    disableRoundCoordinates: true,
                    mapFollowsOnDrag: true,
                    coordinates: coordinates,
                }, markerElement);

                map.addChild(marker);

                flag = true;
            }
        };

        const mapListener = new YMapListener({
            layer: 'any',
            onClick: clickCallback,
        });

        map.addChild(mapListener);
    }
}

function fetchAddressFromCoords(coords) {
    fetch(`https://geocode-maps.yandex.ru/v1/?apikey=${apiKeyCoder}&geocode=${coords[0]},${coords[1]}&format=json`)
        .then(res => res.json())
        .then(data => {
            const featureMember = data.response.GeoObjectCollection.featureMember;

            if (featureMember && featureMember.length > 0) {
                const address = featureMember[0].GeoObject.metaDataProperty.GeocoderMetaData.text;

                document.getElementById(targetInputId).value = address;
            } else {
                console.error("Адрес не найден.");
            }
        })
        .catch(error => {
            console.error('Error fetching geocoding data:', error);
            alert("Ошибка при получении данных с геокодера.");
        });
}

document.getElementById("selectPointA").addEventListener('click', function () {
    targetInputId = 'pointA';
    document.getElementById('map').style.display = 'block';
    document.getElementById('approveAdress').style.display = 'block';
    document.getElementById('selectPointA').style.display = 'none';
    document.getElementById('selectPointB').style.display = 'none';
    initMap();
});

document.getElementById("selectPointB").addEventListener('click', function () {
    targetInputId = 'pointB';
    document.getElementById('map').style.display = 'block';
    document.getElementById('approveAdress').style.display = 'block';
    document.getElementById('selectPointA').style.display = 'none';
    document.getElementById('selectPointB').style.display = 'none';
    initMap();
});


const carTiles = document.querySelectorAll('.car-tile');
const carTypeValue = document.getElementById('carTypeValue');

carTiles.forEach(tile => {
    tile.addEventListener('click', () => {
        carTiles.forEach(t => t.classList.remove('active'));
        tile.classList.add('active');
        carTypeValue.value = tile.dataset.type;
        calculatePrice();
    });
});

document.getElementById("approveAdress").addEventListener('click', function () {
    mapFlag = false;
    document.getElementById('map').style.display = 'none';
    document.getElementById('approveAdress').style.display = 'none';
    document.getElementById('selectPointA').style.display = 'block';
    document.getElementById('selectPointB').style.display = 'block';

    if (targetInputId === 'pointA') {
        fetchAddressFromCoords(coordsA);
    } else {
        fetchAddressFromCoords(coordsB);
    }
    clearBox('map');
})

function clearBox(elementID)
{
    document.getElementById(elementID).innerHTML = "";
}

getUserLocation();
