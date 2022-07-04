
В основной функции handler_func() класса VkAgent используется параметр result[0].
Этот параметр пораждается самой же функцией и он же ей принимается в качестве параметра при следующем цикле.
Данными содержащимимся в этом параметре происходит управление логикой взаимодействия бота с пользователем.
Кроме того, он служит для временного хранения промежуточных данных и передаче их между шагами цикла.
result[0] - хранит данные о текущем пользователе в чате
result[1] - при первом обращении заносится флаг о необходимости запроса возраста при недостатке данных о возрасте.
При последующих обращения хранит информацию о небходимости формирования временного списка подходящих пользователей
result[2] - хранит временный список подходящих пользователей
result[3] - хранит индекс из списка подходящих пользователей к выводу для self.user_id
result[4] - хранит флаг о необходимости прерывания цикла, в котором выполняется функция handler_func,
в случае ожидания сообщения от пользователя
result[5] - хранит флаг, указывающий на необходимость вызова функции обновления данных о возрасте,
после его указания пользователем
result[6] - индекс формируется по ходу выполнения и хранит информацию о только что
выведенном пользователе для занесения его в избранные в случае необходимости
