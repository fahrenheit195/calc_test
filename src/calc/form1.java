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
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.pack();
        frame.setVisible(true);
    }

    public form1() {
        button1.addActionListener(e -> {
            if  (!numCheck(textField1.getText()) || !numCheck(textField2.getText())) {
                textField3.setText("Ошибка входных данных");
                java.awt.Toolkit.getDefaultToolkit().beep();
            } else{ float a = Float.parseFloat(textField1.getText());
                float b = Float.parseFloat(textField2.getText());
                textField3.setText(Float.toString(a / b)); }
        });
    }

    public static Boolean numCheck(String symbol) {
        return symbol.matches("([-+])?\\d*\\.?\\d+");
    }
}
