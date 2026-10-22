plasma_add_applet(org.kde.plasma.battery
    QML_SOURCES main.qml BatteryItem.qml CompactRepresentation.qml InhibitionHint.qml
        InhibitionItem.qml PopupDialog.qml PowerProfileItem.qml LimiteCargaItem.qml
    CPP_SOURCES batteryapplet.cpp
    RESOURCES main.xml
    QML_ARGS NO_CACHEGEN
)
target_link_libraries(org.kde.plasma.battery PRIVATE conservation Qt6::Core KF6::CoreAddons Plasma::Plasma)
add_dependencies(org.kde.plasma.battery translations)
add_executable(test_conservation test_conservation.cpp)
target_link_libraries(test_conservation PRIVATE conservation Qt6::Test)
add_test(NAME conservation COMMAND test_conservation)
set_tests_properties(conservation PROPERTIES ENVIRONMENT "LANGUAGE=en")
add_executable(preview_panel preview_panel.cpp)
target_link_libraries(preview_panel PRIVATE Qt6::Core Qt6::Gui Qt6::Qml Qt6::Quick KF6::I18nQml KF6::I18n)
add_executable(check_applet check_applet.cpp)
target_link_libraries(check_applet PRIVATE Qt6::Gui Plasma::Plasma KF6::CoreAddons)

add_test(NAME conservation_es COMMAND test_conservation)
set_tests_properties(conservation_es PROPERTIES ENVIRONMENT
    "LANGUAGE=es;LC_ALL=en_US.UTF-8;XDG_DATA_DIRS=${CMAKE_BINARY_DIR}/share:/usr/local/share:/usr/share")
