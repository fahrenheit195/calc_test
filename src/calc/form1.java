package calc;

import javax.swing.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;


public class form1 {
    private JButton button1;
    private JPanel panel1;
    private JTextField textField1;
    private JTextField textField2;
    private JTextField textField3;

    public static void main(String[] args) {
        JFrame frame = new JFrame("calc");
        frame.setContentPane(new form1().panel1);
        frame.setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        frame.pack();
        frame.setVisible(true);
    }

    /**
     * Обработчик клика по кнопке
     */
    public form1() {
        button1.addActionListener((ActionEvent e) -> {
            if  (!numCheck(textField1.getText()) || !numCheck(textField2.getText())) {
                textField3.setText("Ошибка входных данных");
                java.awt.Toolkit.getDefaultToolkit().beep();
            } else
            division(Float.parseFloat(textField1.getText()), Float.parseFloat(textField2.getText()));
            if(resCheck(textField3.getText())){
                textField3.setText("Делить на ноль нельзя");
                java.awt.Toolkit.getDefaultToolkit().beep();}
        });
    }

    /**
     * Деление a на b, и вывод в поле реультата
     * @param a делимое
     * @param b делитель
     * @return результат деления
     */
    public float division(float a, float b){
        textField3.setText(Float.toString(a / b));
        return a/b;
    }

    /**
     * Проверка деления на ноль или нуля на ноль
     * @param res выведенный в поле результат деления
     * @return содержит ли сторка данный текст
     */
    public  static  Boolean resCheck(String res) {
        return  res.contains("nfi") || res.contains("NaN");
    }

    /**
     *  Проверка, что введено число
     * @param symbol введеный в поле текст
     * @return результат проверки
     */
    private static Boolean numCheck(String symbol) {
        return symbol.matches("([-+])?\\d*\\.?\\d+");
    }
}